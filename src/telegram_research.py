"""Public Telegram OSINT — no private groups, no deception."""

from __future__ import annotations

import json
from pathlib import Path

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now

QUERIES = [
    "Royale Diamonds",
    "TikTok diamond auctions",
    "lab grown diamond wholesale",
    "LG839637366",
    "royalediamondslive",
]


def research_telegram(
    username: str = "royalediamondslive",
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "telegram"
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        f"https://t.me/{username}",
        f"https://t.me/s/{username}",
        "https://t.me/s/royalediamonds",
        "https://t.me/royalediamonds",
    ]
    pages = []
    for url in candidates:
        meta = collector.get(url, cache_key=f"tg_{url.replace('https://', '').replace('/', '_')}")
        excerpt = ""
        if meta.get("content"):
            path, sha = collector.preserve(
                f"telegram_{url.rstrip('/').split('/')[-1]}.html", meta["content"]
            )
            text = meta["content"].decode("utf-8", errors="ignore")
            excerpt = text[:1500]
            is_channel = b"tgme_channel" in meta["content"] or b"tgme_page_title" in meta["content"]
            pages.append(
                {
                    "url": url,
                    "http_status": meta.get("http_status"),
                    "exists_candidate": bool(is_channel and meta.get("http_status") == 200),
                    "local_path": str(path),
                    "sha256": sha,
                    "excerpt_present": bool(excerpt),
                }
            )
        else:
            pages.append(
                {
                    "url": url,
                    "http_status": meta.get("http_status"),
                    "exists_candidate": False,
                    "error": meta.get("error") or meta.get("status"),
                }
            )

    result = {
        "queries": QUERIES,
        "public_pages": pages,
        "official_vs_impersonator": "UNKNOWN — no confirmed official Telegram channel identified",
        "manual_tasks": [
            {
                "task": "Search TGStat / public Telegram directories for 'Royale Diamonds' and 'royalediamondslive'",
                "status": "PENDING_MANUAL",
                "reason": "No authorized Telethon session configured; avoid private-group access",
            },
            {
                "task": "If a public channel is found, archive announcements and complaint posts with timestamps",
                "status": "PENDING_MANUAL",
            },
        ],
        "collected_at_utc": utc_now().isoformat(),
    }
    (out_dir / "telegram_research.json").write_text(json.dumps(result, indent=2))
    ledger.append(
        EvidenceRecord(
            evidence_id="telegram_public_probe",
            source_url="https://t.me/",
            source_title="Telegram public page probes",
            source_category="telegram",
            reliability=Reliability.C,
            evidence_tier=EvidenceTier.SECONDARY,
            status=ClaimStatus.UNKNOWN,
            extracted_facts={"pages_checked": len(pages)},
            notes="No private groups joined; no deception used.",
        )
    )
    if owns:
        collector.close()
    return result