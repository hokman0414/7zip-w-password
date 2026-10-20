from pathlib import Path

from src.evidence_ledger import EvidenceLedger
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability


def test_ledger_append_only(tmp_path: Path):
    jp = tmp_path / "ledger.json"
    cp = tmp_path / "ledger.csv"
    ledger = EvidenceLedger(json_path=jp, csv_path=cp)
    ledger.append(
        EvidenceRecord(
            evidence_id="e1",
            source_url="https://example.com",
            source_title="Example",
            source_category="test",
            reliability=Reliability.B,
            evidence_tier=EvidenceTier.PRIMARY,
            status=ClaimStatus.CONFIRMED,
        )
    )
    ledger.append(
        EvidenceRecord(
            evidence_id="e1",
            source_url="https://example.com/2",
            source_title="Example2",
            source_category="test",
            reliability=Reliability.C,
            evidence_tier=EvidenceTier.SECONDARY,
            status=ClaimStatus.UNVERIFIED,
        )
    )
    assert len(ledger.records) == 2
    assert jp.exists() and cp.exists()
    reloaded = EvidenceLedger(json_path=jp, csv_path=cp)
    assert len(reloaded.records) == 2