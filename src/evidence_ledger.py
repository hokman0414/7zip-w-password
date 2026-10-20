"""Append-only evidence ledger with CSV/JSON persistence."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Optional

from src.models import EvidenceRecord, utc_now

ROOT = Path(__file__).resolve().parents[1]
LEDGER_JSON = ROOT / "evidence" / "normalized" / "evidence_ledger.json"
LEDGER_CSV = ROOT / "evidence" / "normalized" / "evidence_ledger.csv"
RAW_DIR = ROOT / "evidence" / "raw"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def preserve_bytes(filename: str, data: bytes, subdir: Path = RAW_DIR) -> tuple[Path, str]:
    subdir.mkdir(parents=True, exist_ok=True)
    path = subdir / filename
    path.write_bytes(data)
    return path, sha256_bytes(data)


class EvidenceLedger:
    def __init__(self, json_path: Path = LEDGER_JSON, csv_path: Path = LEDGER_CSV):
        self.json_path = json_path
        self.csv_path = csv_path
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[EvidenceRecord] = []
        if self.json_path.exists():
            self._records = [
                EvidenceRecord.model_validate(r) for r in json.loads(self.json_path.read_text())
            ]

    @property
    def records(self) -> list[EvidenceRecord]:
        return list(self._records)

    def append(self, record: EvidenceRecord) -> EvidenceRecord:
        # append-only: never mutate prior entries; allow duplicate ids with new timestamps
        if not record.collection_timestamp_utc:
            record.collection_timestamp_utc = utc_now()
        self._records.append(record)
        self._persist()
        return record

    def extend(self, records: Iterable[EvidenceRecord]) -> None:
        for r in records:
            self.append(r)

    def find(self, evidence_id: str) -> Optional[EvidenceRecord]:
        for r in reversed(self._records):
            if r.evidence_id == evidence_id:
                return r
        return None

    def _persist(self) -> None:
        payload = [r.model_dump(mode="json") for r in self._records]
        self.json_path.write_text(json.dumps(payload, indent=2, default=str))
        fieldnames = [
            "evidence_id",
            "source_url",
            "source_title",
            "collection_timestamp_utc",
            "publication_timestamp_utc",
            "local_path",
            "sha256",
            "source_category",
            "reliability",
            "evidence_tier",
            "independently_corroborates",
            "status",
            "notes",
        ]
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self._records:
                row = {k: getattr(r, k) for k in fieldnames}
                row["independently_corroborates"] = "|".join(r.independently_corroborates)
                row["collection_timestamp_utc"] = r.collection_timestamp_utc.isoformat()
                if r.publication_timestamp_utc:
                    row["publication_timestamp_utc"] = r.publication_timestamp_utc.isoformat()
                writer.writerow(row)