"""Public business identity OSINT — no private-person profiling."""

from __future__ import annotations

import json
from pathlib import Path

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now


def research_corporate(
    name: str = "Royale Diamonds",
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "business"
    out_dir.mkdir(parents=True, exist_ok=True)

    probes = []
    for label, url in [
        ("opencorporates", "https://opencorporates.com/companies?q=Royale+Diamonds"),
        ("royalediamonds_com", "https://www.royalediamonds.com/"),
        ("uspto_tm_search", "https://tmsearch.uspto.gov/"),
        ("bbb_search", "https://www.bbb.org/search?find_text=Royale%20Diamonds&find_country=US"),
        ("urlscan", "https://urlscan.io/search/#royalediamondslive"),
    ]:
        meta = collector.get(url, cache_key=f"corp_{label}")
        content = meta.get("content") or b""
        if not isinstance(content, (bytes, bytearray)):
            content = str(content).encode("utf-8", errors="ignore")
        blocked = meta.get("http_status") in {403, 429} or (b"recaptcha" in content[:4000].lower())
        status_val = meta.get("status")
        if not isinstance(status_val, (str, int, float, type(None), bool)):
            status_val = str(status_val)
        probes.append(
            {
                "source": label,
                "url": url,
                "http_status": meta.get("http_status"),
                "blocked": bool(blocked),
                "status": "BLOCKED" if blocked else status_val,
            }
        )

    result = {
        "queried_name": name,
        "tiktok_seller_legal_entity": {
            "status": "UNKNOWN",
            "notes": (
                "No public SOS filing conclusively linked to TikTok @royalediamondslive "
                "was verified in this automated pass."
            ),
        },
        "candidate_entities": [
            {
                "name": "Royale Diamonds (Pune, India)",
                "domain": "royalediamonds.com",
                "relation_to_tiktok_seller": "UNVERIFIED name collision",
                "do_not_attribute": True,
            },
            {
                "name": "Royal Diamond USA LLC",
                "domain": "royaldiamondusa.com",
                "relation_to_tiktok_seller": "IRRELEVANT_NAME_COLLISION",
                "do_not_attribute": True,
            },
        ],
        "probes": probes,
        "manual_tasks": [
            {
                "task": "Obtain TikTok Shop seller business name / seller ID from order receipt",
                "why": "Needed to query SOS / OpenCorporates without name-collision risk",
                "status": "NEED_USER_INPUT",
            },
            {
                "task": "Search USPTO / state trademark filings for exact stylized mark used on TikTok",
                "status": "PENDING_MANUAL",
            },
        ],
        "collected_at_utc": utc_now().isoformat(),
    }
    (out_dir / "corporate_research.json").write_text(json.dumps(result, indent=2))
    ledger.append(
        EvidenceRecord(
            evidence_id="corporate_identity",
            source_url="local://corporate_research",
            source_title="Corporate identity assessment",
            source_category="business",
            reliability=Reliability.C,
            evidence_tier=EvidenceTier.SECONDARY,
            status=ClaimStatus.UNKNOWN,
            extracted_facts={"legal_entity": "UNKNOWN"},
            notes="Avoided attributing unrelated similarly named businesses.",
        )
    )
    if owns:
        collector.close()
    return result