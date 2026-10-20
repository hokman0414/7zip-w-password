"""Global diamond inventory correlation for a certificate number."""

from __future__ import annotations

import json
from pathlib import Path

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now

MARKETPLACES = [
    ("ritani", "https://www.ritani.com/search?q={q}"),
    ("brilliance", "https://www.brilliance.com/search?q={q}"),
    ("rarecarat", "https://www.rarecarat.com/"),
    ("jamesallen", "https://www.jamesallen.com/"),
    ("bluenile", "https://www.bluenile.com/"),
    ("withclarity", "https://www.withclarity.com/"),
    ("friendlydiamonds", "https://friendlydiamonds.com/"),
    ("adiamor", "https://www.adiamor.com/"),
    ("loosegrowndiamond", "https://www.loosegrowndiamond.com/"),
    ("stonealgo", "https://stonealgo.com/"),
]


def search_inventory(
    report_number: str = "LG839637366",
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "market"
    out_dir.mkdir(parents=True, exist_ok=True)

    probes = []
    for name, template in MARKETPLACES:
        url = template.format(q=report_number)
        meta = collector.get(url, cache_key=f"inv_{name}_{report_number}")
        body = meta.get("content") or b""
        hit = report_number.encode() in body or report_number.replace("LG", "").encode() in body
        # Cloudflare / bot walls are not negative proof
        blocked = meta.get("http_status") in {403, 429, 503} or b"Just a moment" in body or b"cf-browser-verification" in body
        probes.append(
            {
                "retailer": name,
                "url": url,
                "http_status": meta.get("http_status"),
                "exact_cert_in_html": bool(hit),
                "blocked": blocked,
                "status": "BLOCKED" if blocked else ("POSSIBLE_HIT" if hit else "NO_HIT_IN_HTML"),
            }
        )

    # Seed exact-match matrix from independently collected listing evidence (manual/web search).
    # Only include rows that were actually observed in this investigation.
    matrix = [
        {
            "match_class": "A_same_report_number",
            "report_number": report_number,
            "retailer": "IGI official database",
            "listing_url": f"https://lookup.igi.org/igi_new.php?r={report_number}",
            "price_usd": None,
            "inventory_status": "certificate_exists",
            "specs": {
                "shape": "MARQUISE BRILLIANT",
                "carat": 3.03,
                "color": "F",
                "clarity": "VS1",
                "measurements": "14.39 x 7.67 x 4.78 mm",
                "polish": "VERY GOOD",
                "growth": "CVD",
            },
            "status": "CONFIRMED",
        },
        {
            "match_class": "A_same_report_number",
            "report_number": report_number,
            "retailer": "Ritani",
            "listing_url": None,
            "price_usd": 945.0,
            "wholesale_estimate_usd": 325.97,
            "inventory_status": "lead_not_reproduced",
            "status": "UNVERIFIED",
            "notes": "User-supplied lead; automated Ritani fetch blocked by Cloudflare; search indexes did not surface exact listing.",
        },
        {
            "match_class": "A_same_report_number",
            "report_number": report_number,
            "retailer": "Brilliance",
            "listing_url": None,
            "price_usd": 2020.0,
            "inventory_status": "lead_not_reproduced",
            "status": "UNVERIFIED",
            "notes": "User-supplied lead; public search did not return an exact Brilliance listing for this certificate.",
        },
        {
            "match_class": "C_similar_different_cert",
            "report_number": "LG726561176",
            "retailer": "Jewelry by Cleo",
            "listing_url": "https://jewelrybycleo.com/products/3-03ct-marquise-lab-grown-diamond-colour-f-clarity-vs1-igi-certified",
            "price_usd": 624.0,
            "inventory_status": "listed",
            "specs": {
                "shape": "Marquise",
                "carat": 3.03,
                "color": "F",
                "clarity": "VS1",
                "measurements": "14.76x7.67x4.68mm",
            },
            "status": "CONFIRMED",
        },
        {
            "match_class": "C_similar_different_cert",
            "report_number": "LG747592527",
            "retailer": "Aurélinne",
            "listing_url": "https://aurelinne.com/products/3-03ct-marquise-lab-grown-diamond-colour-f-clarity-vs1-igi-certified-2",
            "price_usd": 736.0,
            "inventory_status": "sold_out",
            "specs": {
                "shape": "Marquise",
                "carat": 3.03,
                "color": "F",
                "clarity": "VS1",
                "measurements": "15.11x7.57x4.68mm",
            },
            "status": "CONFIRMED",
        },
        {
            "match_class": "C_similar_different_cert",
            "report_number": "unknown",
            "retailer": "Laura Milman",
            "listing_url": "https://www.lauramilman.com/products/lg-100759907944",
            "price_usd": 675.0,
            "inventory_status": "listed",
            "specs": {
                "shape": "Marquise",
                "carat": 3.03,
                "color": "F",
                "clarity": "VS1",
                "measurements": "15.75 X 7.55 X 4.52",
            },
            "status": "CONFIRMED",
        },
    ]

    result = {
        "report_number": report_number,
        "marketplace_probes": probes,
        "exact_match_matrix": matrix,
        "shared_feed_hypothesis": (
            "Multiple retailers list similar 3.03ct F/VS1 marquises with different IGI numbers, "
            "consistent with broad wholesale supply — not proof that LG839637366 is multi-listed."
        ),
        "economic_note": (
            "If a ~$326 wholesale estimate were real, a $350 TikTok auction could be near-cost "
            "liquidation; that wholesale figure remains UNVERIFIED."
        ),
        "collected_at_utc": utc_now().isoformat(),
    }
    (out_dir / "inventory_matrix.json").write_text(json.dumps(result, indent=2))
    ledger.append(
        EvidenceRecord(
            evidence_id="inventory_matrix",
            source_url="local://diamond_inventory",
            source_title="Diamond inventory correlation matrix",
            source_category="inventory",
            reliability=Reliability.B,
            evidence_tier=EvidenceTier.SECONDARY,
            status=ClaimStatus.UNVERIFIED,
            extracted_facts={"rows": len(matrix), "blocked_marketplaces": sum(1 for p in probes if p["blocked"])},
        )
    )
    if owns:
        collector.close()
    return result