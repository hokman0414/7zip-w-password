"""Authorized investigation interface: cases, roles, audit chain, retention.

All index access goes through ``InvestigationService``. Every query must be
tied to an open case with a recorded legal/policy basis, and every action is
appended to a hash-chained audit log so tampering is detectable.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .classifier import MalwareClassifier, UnavailableClassifier
from .features import FeatureSet, extract_binary, extract_source
from .index import FingerprintIndex, decide
from .report import build_report

ROLE_PERMISSIONS = {
    "ingestor": {"ingest", "delete"},
    "investigator": {"open_case", "query"},
    "auditor": {"read_audit"},
    "admin": {"ingest", "delete", "purge", "read_audit"},
}


class AccessDenied(PermissionError):
    pass


@dataclass
class Principal:
    name: str
    role: str


@dataclass
class Case:
    case_id: str
    opened_by: str
    basis: str
    scope: str
    opened_at: float
    queries: int = 0
    max_queries: int = 50


class AuditLog:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.entries: list[dict] = []
        self._prev = "0" * 64

    def append(self, actor: str, action: str, **details) -> dict:
        entry = {"ts": time.time(), "actor": actor, "action": action, "details": details, "prev": self._prev}
        digest = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        entry["hash"] = digest
        self._prev = digest
        self.entries.append(entry)
        if self.path:
            with self.path.open("a") as fh:
                fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            body = {k: v for k, v in e.items() if k != "hash"}
            if body["prev"] != prev:
                return False
            if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != e["hash"]:
                return False
            prev = e["hash"]
        return True


@dataclass
class Thresholds:
    min_score: float = 8.0
    min_margin: float = 2.0
    min_distinct: int = 3


@dataclass
class InvestigationService:
    index: FingerprintIndex
    audit: AuditLog = field(default_factory=AuditLog)
    classifier: MalwareClassifier = field(default_factory=UnavailableClassifier)
    thresholds: Thresholds = field(default_factory=Thresholds)
    cases: dict[str, Case] = field(default_factory=dict)

    def _require(self, who: Principal, perm: str) -> None:
        if perm not in ROLE_PERMISSIONS.get(who.role, set()):
            self.audit.append(who.name, "denied", permission=perm, role=who.role)
            raise AccessDenied(f"{who.name} ({who.role}) lacks permission '{perm}'")

    def ingest_source(self, who: Principal, ref: str, code: str, ttl_seconds: float | None = None) -> None:
        self._require(who, "ingest")
        fs = extract_source(code)
        self.index.add(ref, fs.features, ttl_seconds=ttl_seconds)
        self.audit.append(who.name, "ingest", ref=ref, n_features=len(fs.features), ttl=ttl_seconds)

    def delete_record(self, who: Principal, ref: str) -> bool:
        self._require(who, "delete")
        ok = self.index.delete(ref)
        self.audit.append(who.name, "delete", ref=ref, existed=ok)
        return ok

    def purge_expired(self, who: Principal, now: float | None = None) -> list[str]:
        self._require(who, "purge")
        removed = self.index.purge_expired(now)
        self.audit.append(who.name, "purge", removed=len(removed))
        return removed

    def open_case(self, who: Principal, basis: str, scope: str) -> Case:
        self._require(who, "open_case")
        if len(basis.strip()) < 10:
            raise ValueError("a documented authorization basis is required to open a case")
        case = Case(uuid.uuid4().hex[:12], who.name, basis, scope, time.time())
        self.cases[case.case_id] = case
        self.audit.append(who.name, "open_case", case_id=case.case_id, basis=basis, scope=scope)
        return case

    def investigate(self, who: Principal, case_id: str, artifact: Path | str, artifact_kind: str = "binary") -> dict:
        self._require(who, "query")
        case = self.cases.get(case_id)
        if case is None:
            raise AccessDenied("query requires an open case")
        if case.queries >= case.max_queries:
            raise AccessDenied("case query budget exhausted; re-authorization required")
        case.queries += 1
        artifact = Path(artifact)
        sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if artifact_kind == "binary":
            fs: FeatureSet = extract_binary(artifact)
        else:
            fs = extract_source(artifact.read_text())
        cands = self.index.search(fs.features, top_k=10)
        t = self.thresholds
        decision = decide(cands, t.min_score, t.min_margin, t.min_distinct)
        signal = self.classifier.score(artifact)
        plaintext = {self.index.keyed(f): f for f in fs.features}
        report = build_report(case, artifact.name, sha256, fs, cands, decision, signal, plaintext)
        self.audit.append(
            who.name, "query", case_id=case_id, artifact_sha256=sha256,
            escalated=decision.escalate, top_ref=decision.top.ref if decision.escalate and decision.top else None,
        )
        return report
