"""Keyed fingerprint index and candidate ranking.

Records hold only keyed hashes of features (HMAC with an index-owner key), an
opaque record reference, and retention metadata. Raw code and conversation
content are never stored. Low-entropy features (common constants, libc names)
remain guessable by anyone who holds the key, so the key must stay with the
data owner (e.g. the AI provider or the IP owner).
"""

from __future__ import annotations

import hashlib
import hmac
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field

TYPE_WEIGHTS = {"s": 1.0, "c": 0.6, "f": 0.8, "i": 0.1, "w": 0.5}


def _ftype(feature: str) -> str:
    return feature.split(":", 1)[0]


@dataclass
class Record:
    ref: str
    hashed: dict[str, str]  # keyed hash -> feature type
    created_at: float
    expires_at: float | None
    meta: dict = field(default_factory=dict)


@dataclass
class Candidate:
    ref: str
    score: float
    containment: float
    matched: list[str]  # keyed hashes
    matched_by_type: dict[str, int]


class FingerprintIndex:
    def __init__(self, key: bytes, hash_bytes: int = 12):
        if len(key) < 16:
            raise ValueError("index key must be at least 16 bytes")
        self._key = key
        self._hash_bytes = hash_bytes
        self.records: dict[str, Record] = {}
        self._postings: dict[str, set[str]] = defaultdict(set)

    def keyed(self, feature: str) -> str:
        return hmac.new(self._key, feature.encode(), hashlib.sha256).digest()[: self._hash_bytes].hex()

    def add(self, ref: str, features: set[str], ttl_seconds: float | None = None, meta: dict | None = None) -> None:
        if ref in self.records:
            self.delete(ref)
        now = time.time()
        hashed = {self.keyed(f): _ftype(f) for f in features}
        self.records[ref] = Record(ref, hashed, now, now + ttl_seconds if ttl_seconds else None, meta or {})
        for h in hashed:
            self._postings[h].add(ref)

    def delete(self, ref: str) -> bool:
        rec = self.records.pop(ref, None)
        if rec is None:
            return False
        for h in rec.hashed:
            post = self._postings.get(h)
            if post is not None:
                post.discard(ref)
                if not post:
                    del self._postings[h]
        return True

    def purge_expired(self, now: float | None = None) -> list[str]:
        now = time.time() if now is None else now
        expired = [r.ref for r in self.records.values() if r.expires_at is not None and r.expires_at <= now]
        for ref in expired:
            self.delete(ref)
        return expired

    def idf(self, h: str) -> float:
        n = max(1, len(self.records))
        df = len(self._postings.get(h, ()))
        return math.log((n + 1) / (df + 1)) + 1e-6

    def storage_bytes(self) -> int:
        per_hash = self._hash_bytes + 1
        return sum(len(r.hashed) * per_hash + len(r.ref) + 16 for r in self.records.values())

    def search(
        self,
        features: set[str],
        top_k: int = 10,
        types: set[str] | None = None,
        max_df_fraction: float = 0.05,
    ) -> list[Candidate]:
        """Rank records by IDF-weighted shared evidence.

        ``score`` is the summed weighted IDF of shared features. Features that
        occur in more than ``max_df_fraction`` of records are ignored: they are
        boilerplate and only produce coincidental matches.
        """
        n = max(1, len(self.records))
        df_cap = max(2, int(n * max_df_fraction))
        q: dict[str, str] = {}
        for f in features:
            t = _ftype(f)
            if types is None or t in types:
                q[self.keyed(f)] = t
        scores: dict[str, float] = defaultdict(float)
        matched: dict[str, list[str]] = defaultdict(list)
        for h, t in q.items():
            post = self._postings.get(h)
            if not post or len(post) > df_cap:
                continue
            w = TYPE_WEIGHTS.get(t, 0.5) * self.idf(h)
            for ref in post:
                scores[ref] += w
                matched[ref].append(h)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        out = []
        for ref, s in ranked:
            rec = self.records[ref]
            denom = sum(
                TYPE_WEIGHTS.get(t, 0.5) * self.idf(h)
                for h, t in rec.hashed.items()
                if (types is None or t in types) and len(self._postings.get(h, ())) <= df_cap
            )
            by_type: dict[str, int] = defaultdict(int)
            for h in matched[ref]:
                by_type[rec.hashed[h]] += 1
            out.append(Candidate(ref, s, s / denom if denom else 0.0, matched[ref], dict(by_type)))
        return out


@dataclass
class Decision:
    escalate: bool
    reason: str
    top: Candidate | None
    margin: float


def decide(cands: list[Candidate], min_score: float, min_margin: float = 0.0, min_distinct: int = 2) -> Decision:
    """Open-set decision: abstain unless evidence is strong *and* unambiguous."""
    if not cands:
        return Decision(False, "no candidate shares any distinctive feature", None, 0.0)
    top = cands[0]
    second = cands[1].score if len(cands) > 1 else 0.0
    margin = top.score - second
    if len(top.matched) < min_distinct:
        return Decision(False, f"only {len(top.matched)} distinctive feature(s) shared", top, margin)
    if top.score < min_score:
        return Decision(False, f"evidence score {top.score:.2f} below threshold {min_score:.2f}", top, margin)
    if margin < min_margin:
        return Decision(False, f"ambiguous: margin {margin:.2f} over runner-up below {min_margin:.2f}", top, margin)
    return Decision(True, "evidence threshold met; requires human review", top, margin)
