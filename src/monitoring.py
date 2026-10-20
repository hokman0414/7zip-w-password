"""Order and shipment monitoring using user-provided tracking details."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now

USPS_URL = "https://tools.usps.com/go/TrackConfirmAction?tLabels={tn}"
PARCELS_URL = "https://parcelsapp.com/en/tracking/{tn}"


def classify_usps_number(tn: str) -> dict:
    tn = re.sub(r"\s+", "", tn)
    ok = bool(re.fullmatch(r"9[2-5]\d{18,22}", tn))
    return {
        "tracking_number": tn,
        "format_looks_like_usps": ok,
        "carrier_guess": "USPS" if ok else "UNKNOWN",
    }


def monitor_order(
    case_id: str = "royale_diamonds",
    tracking_number: str | None = None,
    purchase_date: str = "2026-10-19",
    ship_by_date: str | None = None,
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "case_id": case_id,
        "purchase_date": purchase_date,
        "order_status": "PAID_VIA_TIKTOK_SHOP_USER_REPORTED",
        "seller_promised_ship_by_date": ship_by_date,
        "tracking_number": tracking_number,
        "carrier": None,
        "shipment_status": "Tracking not yet issued — shipment status unverified."
        if not tracking_number
        else "UNKNOWN",
        "delivery_status": "NOT_DELIVERED_UNVERIFIED",
        "refund_eligibility": {
            "note": "TikTok livestream auction purchases often final sale; disputes may still apply if not as described / non-delivery.",
            "action": "Check TikTok Shop order detail for return window and open dispute deadlines",
        },
        "probes": [],
        "collected_at_utc": utc_now().isoformat(),
    }

    if tracking_number:
        fmt = classify_usps_number(tracking_number)
        state["carrier"] = fmt["carrier_guess"]
        state["tracking_format"] = fmt

        usps = collector.get(USPS_URL.format(tn=tracking_number), cache_key=f"usps_{tracking_number}")
        parcels = collector.get(
            PARCELS_URL.format(tn=tracking_number), cache_key=f"parcels_{tracking_number}"
        )
        state["probes"].append(
            {
                "source": "usps",
                "url": USPS_URL.format(tn=tracking_number),
                "http_status": usps.get("http_status"),
                "status": usps.get("status"),
                "blocked": usps.get("http_status") in {403, 429}
                or (usps.get("content") and b"Access Denied" in usps["content"]),
            }
        )
        parcels_text = (parcels.get("content") or b"").decode("utf-8", errors="ignore")
        no_info = "No information about your package" in parcels_text
        state["probes"].append(
            {
                "source": "parcelsapp",
                "url": PARCELS_URL.format(tn=tracking_number),
                "http_status": parcels.get("http_status"),
                "no_information": no_info,
            }
        )
        if no_info:
            state["shipment_status"] = (
                "NO_PUBLIC_SCAN_DATA — aggregator reports no information; "
                "USPS authoritative portal blocked from this environment. "
                "Do not infer transit progress."
            )
            status = ClaimStatus.UNKNOWN
        elif state["probes"][0]["blocked"]:
            state["shipment_status"] = (
                "USPS portal blocked (Access Denied). Tracking status unverified from this host."
            )
            status = ClaimStatus.BLOCKED
        else:
            status = ClaimStatus.UNVERIFIED

        ledger.append(
            EvidenceRecord(
                evidence_id=f"tracking_{tracking_number}",
                source_url=PARCELS_URL.format(tn=tracking_number),
                source_title="Shipment tracking probe",
                source_category="shipping",
                reliability=Reliability.C,
                evidence_tier=EvidenceTier.SECONDARY,
                status=status,
                extracted_facts={
                    "tracking_number": tracking_number,
                    "shipment_status": state["shipment_status"],
                },
                notes="Never infer progress from unrelated tracking numbers.",
            )
        )

    path = out_dir / f"monitoring_{case_id}.json"
    path.write_text(json.dumps(state, indent=2))
    if owns:
        collector.close()
    return state