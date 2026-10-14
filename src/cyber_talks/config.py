from __future__ import annotations

import json
from pathlib import Path

import yaml

from cyber_talks.models import Conference

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CONFERENCE_REGISTRY = DATA / "conferences" / "registry.json"
TOPICS_FILE = DATA / "topics" / "keywords.yaml"
OUTPUT_DIR = DATA / "output"


def load_registry(path: Path | None = None) -> dict:
    p = path or CONFERENCE_REGISTRY
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def load_conferences(path: Path | None = None) -> list[Conference]:
    data = load_registry(path)
    return [Conference.model_validate(c) for c in data.get("conferences", [])]


def load_topic_config(path: Path | None = None) -> dict:
    p = path or TOPICS_FILE
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_output_dir(path: Path | None = None) -> Path:
    out = path or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcripts").mkdir(parents=True, exist_ok=True)
    (out / "talks").mkdir(parents=True, exist_ok=True)
    return out
