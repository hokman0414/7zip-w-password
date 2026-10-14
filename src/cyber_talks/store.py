from __future__ import annotations

import json
from pathlib import Path

from cyber_talks.models import TalkCandidate, TalkRecord


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_candidates(path: Path, candidates: list[TalkCandidate]) -> None:
    write_jsonl(path, [c.model_dump() for c in candidates])


def save_talk_record(out_dir: Path, record: TalkRecord) -> Path:
    talks_dir = out_dir / "talks"
    talks_dir.mkdir(parents=True, exist_ok=True)
    path = talks_dir / f"{record.video_id}.json"
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    if record.transcript_text:
        tdir = out_dir / "transcripts"
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / f"{record.video_id}.txt").write_text(record.transcript_text, encoding="utf-8")
    return path


def load_seen_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            vid = obj.get("video_id")
            if vid:
                seen.add(vid)
    return seen


def write_index(out_dir: Path, records: list[TalkRecord]) -> Path:
    index = []
    for r in records:
        index.append(
            {
                "video_id": r.video_id,
                "title": r.title,
                "url": r.url,
                "conference": r.conference_name,
                "conference_id": r.conference_id,
                "upload_date": r.upload_date,
                "score": r.score,
                "topics": [t.topic for t in r.topics],
                "speakers": [s.name for s in r.speakers if s.name],
                "transcript_source": r.transcript_source,
                "transcript_chars": len(r.transcript_text or ""),
                "channel": r.channel,
            }
        )
    path = out_dir / "index.json"
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    write_jsonl(out_dir / "index.jsonl", index)
    return path
