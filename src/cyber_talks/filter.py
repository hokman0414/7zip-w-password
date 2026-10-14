from __future__ import annotations

import re
from datetime import datetime, timezone

from cyber_talks.models import TalkCandidate, TopicMatch


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _term_match(term: str, blob: str) -> bool:
    """Substring match for multi-word phrases; word-boundary for short tokens."""
    t = _norm(term)
    if not t:
        return False
    if " " in t or len(t) >= 6:
        return t in blob
    return re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", blob) is not None


def score_talk(
    candidate: TalkCandidate,
    topic_config: dict,
    *,
    min_score: float = 3.0,
    since: datetime | None = None,
) -> TalkCandidate | None:
    """Attach topic matches + score. Return None if below threshold or too old."""
    if since:
        dt = candidate.upload_datetime
        if dt and dt.replace(tzinfo=timezone.utc) < since.replace(tzinfo=timezone.utc):
            return None

    blob = _norm(f"{candidate.title} {candidate.description} {candidate.channel}")
    topics_cfg = topic_config.get("topics", {})
    matches: list[TopicMatch] = []
    score = 0.0

    for topic_name, meta in topics_cfg.items():
        weight = int(meta.get("weight", 1))
        hit_terms: list[str] = []
        for term in meta.get("terms", []):
            if _term_match(term, blob):
                hit_terms.append(term)
        if hit_terms:
            # Diminishing returns for many hits in same topic
            topic_score = weight * (1.0 + 0.25 * (len(set(hit_terms)) - 1))
            score += topic_score
            matches.append(
                TopicMatch(topic=topic_name, weight=weight, matched_terms=sorted(set(hit_terms)))
            )

    # Boost when conference cues present
    cue_hits = 0
    for cue in topic_config.get("conference_cues", []):
        if _norm(cue) in blob:
            cue_hits += 1
    if cue_hits:
        score += min(2.0, 0.5 * cue_hits)

    # Soft-penalize noise-only titles
    noise = topic_config.get("noise_terms", [])
    noise_hits = sum(1 for n in noise if _norm(n) in blob)
    if noise_hits and not matches:
        return None
    score -= 0.5 * noise_hits

    if score < min_score or not matches:
        return None

    candidate.topics = matches
    candidate.score = round(score, 2)
    return candidate


def filter_candidates(
    candidates: list[TalkCandidate],
    topic_config: dict,
    *,
    min_score: float = 3.0,
    since: datetime | None = None,
) -> list[TalkCandidate]:
    kept: list[TalkCandidate] = []
    seen: set[str] = set()
    for c in candidates:
        if c.video_id in seen:
            continue
        scored = score_talk(c, topic_config, min_score=min_score, since=since)
        if scored:
            seen.add(scored.video_id)
            kept.append(scored)
    kept.sort(key=lambda x: (-x.score, x.upload_date or ""))
    return kept
