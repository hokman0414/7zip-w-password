"""Source discovery planner and resumable task list."""

from __future__ import annotations

import json
from pathlib import Path

from src.models import utc_now

DEFAULT_SOURCES = [
    {"id": "igi", "category": "diamond_cert", "url": "https://lookup.igi.org/", "priority": 1},
    {"id": "tiktok_profile", "category": "tiktok", "url": "https://www.tiktok.com/@royalediamondslive", "priority": 1},
    {"id": "mashable", "category": "media", "url": "https://mashable.com/life/tiktok-shop-lab-grown-diamond-live-auctions", "priority": 2},
    {"id": "usps", "category": "shipping", "url": "https://tools.usps.com/", "priority": 1},
    {"id": "ritani", "category": "inventory", "url": "https://www.ritani.com/", "priority": 2},
    {"id": "brilliance", "category": "inventory", "url": "https://www.brilliance.com/", "priority": 2},
    {"id": "opencorporates", "category": "business", "url": "https://opencorporates.com/", "priority": 3},
    {"id": "telegram", "category": "telegram", "url": "https://t.me/", "priority": 3},
]


def discover_sources(case_id: str = "royale_diamonds") -> dict:
    root = Path(__file__).resolve().parents[1]
    out = {
        "case_id": case_id,
        "sources": DEFAULT_SOURCES,
        "manual_tasks": [
            {"id": "manual_igi_pdf", "task": "Download official IGI PDF in interactive browser if API PDF blocked", "status": "OPTIONAL"},
            {"id": "manual_usps", "task": "Open USPS tracking in user browser and save screenshot", "status": "RECOMMENDED"},
            {"id": "manual_order_receipt", "task": "Provide TikTok Shop order ID, seller legal name, ship-by date", "status": "NEED_USER_INPUT"},
            {"id": "manual_ritani", "task": "Reproduce Ritani listing for LG839637366 if still claimed", "status": "PENDING"},
        ],
        "collected_at_utc": utc_now().isoformat(),
    }
    path = root / "data" / f"source_discovery_{case_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    return out