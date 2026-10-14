from __future__ import annotations

import re

from cyber_talks.models import SpeakerAttribution, TalkCandidate

# Common patterns in conference talk titles:
# "Talk Title - Speaker Name"
# "Talk Title | Speaker"
# "Speaker Name: Talk Title"
# "CONF 2024 - Title (Speaker)"

_SPLIT_DASH = re.compile(r"\s+[-–—]\s+")
_SPLIT_PIPE = re.compile(r"\s+\|\s+")
_PAREN_SPEAKER = re.compile(r"\(([^)]{2,80})\)\s*$")
_BY_SPEAKER = re.compile(r"\bby\s+([A-Z][\w .'-]{1,60})$", re.I)


def extract_speakers(candidate: TalkCandidate) -> list[SpeakerAttribution]:
    title = (candidate.title or "").strip()
    desc = (candidate.description or "").strip()
    speakers: list[SpeakerAttribution] = []

    paren = _PAREN_SPEAKER.search(title)
    if paren:
        speakers.append(SpeakerAttribution(name=paren.group(1).strip(), raw_credit=paren.group(0)))

    by_m = _BY_SPEAKER.search(title)
    if by_m:
        speakers.append(SpeakerAttribution(name=by_m.group(1).strip(), raw_credit=by_m.group(0)))

    # "Conf 2024: Speaker Name - Talk Title"
    colon = re.match(
        r"^[^:]{3,60}:\s*([A-Z][\w .'-]{1,50})\s*[-–—]\s*.+$",
        title,
    )
    if colon:
        speakers.append(SpeakerAttribution(name=colon.group(1).strip(), raw_credit=title))

    # Dash / pipe splits: prefer right-hand side when short and looks like a name
    for splitter in (_SPLIT_DASH, _SPLIT_PIPE):
        parts = splitter.split(title)
        if len(parts) >= 2:
            rhs = parts[-1].strip()
            lhs = parts[0].strip()
            # Heuristic: speaker side is shorter and lacks year-like conference codes alone
            if 2 <= len(rhs) <= 60 and not re.search(r"\b20\d{2}\b", rhs):
                # Avoid treating "DEF CON 32" style left remnants as speakers when RHS is long title
                if len(rhs.split()) <= 6 and not re.search(
                    r"\b(detection|threat|security|engineering|hunting|analysis)\b",
                    rhs,
                    re.I,
                ):
                    speakers.append(SpeakerAttribution(name=rhs, raw_credit=title))
            # Left side after conference prefix may be the speaker
            left_speaker = re.search(
                r"(?:20\d{2}|CON|DEF CON|BSides)\s*[-:]?\s*([A-Z][\w .'-]{1,40})\s*$",
                lhs,
                re.I,
            )
            if left_speaker and len(left_speaker.group(1).split()) <= 4:
                speakers.append(
                    SpeakerAttribution(name=left_speaker.group(1).strip(), raw_credit=title)
                )

    # Description lines like "Speaker: Jane Doe" / "Presented by ..."
    for line in desc.splitlines()[:40]:
        line = line.strip()
        m = re.match(r"^(?:speakers?|presented by|author|presenter)\s*[:\-]\s*(.+)$", line, re.I)
        if m:
            name = m.group(1).strip()
            # Split multi-speaker lists
            for piece in re.split(r"\s*(?:,|&| and )\s*", name):
                piece = piece.strip()
                if 2 <= len(piece) <= 80:
                    speakers.append(SpeakerAttribution(name=piece, raw_credit=line))

    # Dedup by normalized name
    seen: set[str] = set()
    unique: list[SpeakerAttribution] = []
    for s in speakers:
        key = (s.name or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(s)
    return unique[:8]


def build_attribution(candidate: TalkCandidate, speakers: list[SpeakerAttribution]) -> dict:
    return {
        "video_id": candidate.video_id,
        "url": candidate.url,
        "channel": candidate.channel,
        "channel_id": candidate.channel_id,
        "conference_id": candidate.conference_id,
        "conference_name": candidate.conference_name,
        "upload_date": candidate.upload_date,
        "speakers": [s.model_dump() for s in speakers],
        "discovery_method": candidate.discovery_method,
        "topics": [t.model_dump() for t in candidate.topics],
        "score": candidate.score,
        "license_note": (
            "Transcripts are scraped from publicly available YouTube captions. "
            "Respect YouTube ToS, conference copyrights, and speaker rights. "
            "Use for personal research; redistribute only if permitted."
        ),
    }
