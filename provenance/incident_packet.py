"""Neutral, consent-gated incident evidence packets for AI providers (Cycle 6).

A victim (or its incident responder) shares artifacts from an intrusion. The
broker turns them into one packet per AI provider whose service the artifacts
show being used, shaped like the third-party-suppliable fields of an EU GPAI
Code of Practice serious-incident report (Measure 9.2):

    period, chain_of_events, model_involved, material_on_model_involvement,
    provider_to_complete, limitations

Rules enforced here:

* No packet without a recorded, unexpired victim consent naming the provider.
* Victim identifiers (IPs, emails, internal hosts, account names, user paths,
  and any terms the victim lists) are replaced with case-keyed pseudonyms.
* Credentials are never copied; packets carry provider + redacted form only.
* Provider neutrality: a provider's packet contains nothing about any other
  provider (their endpoints, models and keys are masked as <other-provider>).
* Every packet build is written to the hash-chained audit log.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass, field

from .llm_indicators import CREDENTIAL_PATTERNS, ENDPOINTS, MODEL_RE, scan_bytes
from .service import AccessDenied, AuditLog, Principal

# Open-weight families (qwen, llama, ...) are served by many hosts, so a model
# name alone cannot route them to one provider.
MODEL_FAMILY = {
    "gpt-": "openai", "claude-": "anthropic", "gemini-": "google",
    "deepseek-": "deepseek", "mistral-": "mistral",
}

_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Requires "::" or a hex letter so clock times like 08:00:00 are not matched.
_IPV6 = re.compile(r"(?<![\w:])(?=[0-9A-Fa-f:]*(?:::|[A-Fa-f]))(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_DOMAIN_USER = re.compile(r"\b[A-Z][A-Z0-9-]{1,14}\\[\w.$-]+")
_USER_PATH = re.compile(r"(?i)(?<=[\\/]users[\\/])[^\\/\s\"']+|(?<=/home/)[^/\s\"']+")
_TS = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b")


@dataclass(frozen=True)
class VictimConsent:
    case_id: str
    granted_by: str
    providers: frozenset[str]
    internal_domains: tuple[str, ...]
    sensitive_terms: tuple[str, ...] = ()
    harm_summary: str = ""
    expires_at: float = float("inf")


@dataclass
class IncidentBroker:
    pseudonym_key: bytes
    fingerprint_key: bytes
    audit: AuditLog = field(default_factory=AuditLog)
    consents: dict[str, VictimConsent] = field(default_factory=dict)

    def record_consent(self, who: Principal, consent: VictimConsent) -> None:
        self._require(who)
        self.consents[consent.case_id] = consent
        self.audit.append(
            who.name, "consent", case_id=consent.case_id, granted_by=consent.granted_by,
            providers=sorted(consent.providers), expires_at=consent.expires_at,
        )

    def _require(self, who: Principal) -> None:
        if who.role != "investigator":
            self.audit.append(who.name, "denied", permission="incident_packet", role=who.role)
            raise AccessDenied(f"{who.name} ({who.role}) may not build incident packets")

    def _pseudo(self, case_id: str, kind: str, value: str) -> str:
        tag = hmac.new(self.pseudonym_key, f"{case_id}|{kind}|{value.lower()}".encode(), hashlib.sha256)
        return f"<{kind}:{tag.hexdigest()[:8]}>"

    def redact(self, case_id: str, text: str, consent: VictimConsent) -> str:
        for provider, pattern in CREDENTIAL_PATTERNS.items():
            text = re.sub(pattern.pattern.decode(), lambda m, p=provider: f"<{p}-key:...{m.group()[-4:]}>", text)
        for term in sorted(consent.sensitive_terms, key=len, reverse=True):
            text = re.sub(re.escape(term), lambda m: self._pseudo(case_id, "term", m.group()), text, flags=re.I)
        text = _EMAIL.sub(lambda m: self._pseudo(case_id, "email", m.group()), text)
        for dom in consent.internal_domains:
            host_re = re.compile(r"\b[\w-]+(?:\.[\w-]+)*\." + re.escape(dom) + r"\b|\b" + re.escape(dom) + r"\b", re.I)
            text = host_re.sub(lambda m: self._pseudo(case_id, "host", m.group()), text)
        text = _DOMAIN_USER.sub(lambda m: self._pseudo(case_id, "account", m.group()), text)
        text = _USER_PATH.sub(lambda m: self._pseudo(case_id, "user", m.group()), text)
        text = _IPV6.sub(lambda m: self._pseudo(case_id, "ip", m.group()), text)
        text = _IPV4.sub(lambda m: self._pseudo(case_id, "ip", m.group()), text)
        return text

    @staticmethod
    def _mask_other_providers(line: str, keep: str) -> str:
        for host, provider in ENDPOINTS.items():
            if provider != keep:
                line = re.sub(re.escape(host.decode()), "<other-provider>", line, flags=re.I)
        line = re.sub(r"<(?!%s-key)[a-z]+-key:\.\.\.[^>]{4}>" % re.escape(keep), "<other-provider>", line)

        def model_sub(m: re.Match) -> str:
            name = m.group().lower()
            fam = next((p for prefix, p in MODEL_FAMILY.items() if name.startswith(prefix)), None)
            return m.group() if fam in (keep, None) else "<other-provider>"

        return re.sub(MODEL_RE.pattern.decode(), model_sub, line, flags=re.I)

    def build_packets(
        self, who: Principal, case_id: str, artifacts: dict[str, bytes], logs: list[str], now: float | None = None
    ) -> dict[str, dict]:
        self._require(who)
        consent = self.consents.get(case_id)
        now = time.time() if now is None else now
        if consent is None or consent.expires_at <= now:
            self.audit.append(who.name, "denied", permission="incident_packet", case_id=case_id, reason="no consent")
            raise AccessDenied("incident packets require recorded, unexpired victim consent")

        evidence: dict[str, list[dict]] = {}
        models: dict[str, set[str]] = {}
        for name, data in artifacts.items():
            r = scan_bytes(data, self.fingerprint_key)
            for c in r.credentials:
                evidence.setdefault(c.provider, []).append(
                    {"artifact_sha256": r.sha256, "kind": "credential", "redacted": c.redacted, "offset": c.offset}
                )
            for provider, hosts in r.endpoints.items():
                for h in sorted(hosts):
                    evidence.setdefault(provider, []).append({"artifact_sha256": r.sha256, "kind": "endpoint", "value": h})
            for m in r.models:
                fam = next((p for prefix, p in MODEL_FAMILY.items() if m.startswith(prefix)), None)
                if fam:
                    models.setdefault(fam, set()).add(m)

        redacted_lines = [self.redact(case_id, line, consent) for line in logs]
        for line in redacted_lines:
            low = line.lower()
            for host, provider in ENDPOINTS.items():
                if host.decode() in low:
                    evidence.setdefault(provider, []).append({"kind": "log-endpoint", "value": host.decode()})
            for provider in CREDENTIAL_PATTERNS:
                for m in re.finditer(r"<%s-key:\.\.\.[^>]{4}>" % provider, line):
                    evidence.setdefault(provider, []).append({"kind": "log-credential", "redacted": m.group()})
            for m in re.finditer(MODEL_RE.pattern.decode(), line, flags=re.I):
                name = m.group().lower()
                fam = next((p for prefix, p in MODEL_FAMILY.items() if name.startswith(prefix)), None)
                if fam:
                    models.setdefault(fam, set()).add(name)

        stamps = sorted(ts for line in redacted_lines for ts in _TS.findall(line))
        packets: dict[str, dict] = {}
        for provider in sorted(set(evidence) | set(models)):
            if provider not in consent.providers:
                self.audit.append(who.name, "withheld", case_id=case_id, provider=provider, reason="outside consent")
                continue
            packet = {
                "case_ref": self._pseudo(case_id, "case", case_id),
                "provider": provider,
                "period": {"start": stamps[0] if stamps else None, "end": stamps[-1] if stamps else None},
                "harm_and_affected_group": self.redact(case_id, consent.harm_summary, consent),
                "chain_of_events": [self._mask_other_providers(line, provider) for line in redacted_lines],
                "model_involved": sorted(models.get(provider, set())),
                "material_on_model_involvement": evidence.get(provider, []),
                "provider_to_complete": [
                    "root cause: model inputs/outputs that led to the incident (Measure 9.2 point 8)",
                    "accounts/sessions linked to the material above",
                    "response and corrective measures",
                ],
                "limitations": [
                    "Indicators show the attacker configured or called this provider's service; they do not prove "
                    "this provider's model wrote the attack code.",
                    "A credential may belong to a victim whose key was stolen or resold (LLMjacking).",
                    "Maliciousness of artifacts was established by human analysis, not by indicators or ML scores.",
                ],
            }
            digest = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
            packets[provider] = packet
            self.audit.append(who.name, "packet", case_id=case_id, provider=provider, packet_sha256=digest)
        return packets
