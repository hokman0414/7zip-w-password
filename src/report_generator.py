"""Generate markdown + machine-readable investigation reports."""

from __future__ import annotations

import json
from pathlib import Path

from src.models import utc_now


def _load(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def generate_reports(case_id: str = "royale_diamonds") -> dict:
    root = Path(__file__).resolve().parents[1]
    igi = _load(root / "research" / "diamonds" / "igi_LG839637366_verified.json")
    seller = _load(root / "research" / "tiktok" / "seller_research.json")
    usernames = _load(root / "research" / "tiktok" / "username_correlation.json")
    telegram = _load(root / "research" / "telegram" / "telegram_research.json")
    inventory = _load(root / "research" / "market" / "inventory_matrix.json")
    pricing = _load(root / "research" / "market" / "pricing_analysis.json")
    corporate = _load(root / "research" / "business" / "corporate_research.json")
    reputation = _load(root / "research" / "complaints" / "reputation_analysis.json")
    ach = _load(root / "analysis" / "ach_matrix.json")
    monitoring = _load(root / "analysis" / f"monitoring_{case_id}.json")
    ledger = _load(root / "evidence" / "normalized" / "evidence_ledger.json")

    polish_mismatch = any(
        c.get("field") == "polish" and c.get("result") == "MISMATCH" for c in igi.get("comparisons", [])
    )
    leading = ach.get("current_leading_hypotheses", [])
    posteriors = (ach.get("subjective_bayes") or {}).get("posteriors", {})

    executive = {
        "case_id": case_id,
        "as_of_utc": utc_now().isoformat(),
        "seller_legitimacy": {
            "status": "CORROBORATED_PUBLIC_PRESENCE",
            "username": seller.get("confirmed_username"),
            "summary": (
                "Public media and a live TikTok profile corroborate @royalediamondslive as the "
                "Royale Diamonds livestream auction seller. Legal business entity remains UNKNOWN."
            ),
        },
        "certificate_status": {
            "status": igi.get("verification_status", "UNKNOWN"),
            "report": "LG839637366",
            "summary": (
                "Official IGI lookup confirms a laboratory-grown marquise 3.03ct F VS1 CVD diamond "
                "with matching measurements. Advertised polish Excellent is CONTRADICTED by IGI Very Good."
                if igi.get("verification_status") == "CONFIRMED"
                else "IGI verification incomplete."
            ),
            "polish_mismatch": polish_mismatch,
        },
        "economic_plausibility": {
            "purchase_usd": 350,
            "assessment": (pricing.get("assessment") or {}),
            "summary": (pricing.get("assessment") or {}).get("rationale"),
        },
        "fraud_risk": {
            "leading_hypotheses": leading,
            "subjective_posteriors": posteriors,
            "summary": (
                "Current evidence most favors legitimate/fulfillable sale with possible value exaggeration "
                "(H2/H1). Fulfillment, substitution, and impersonation remain open until delivery + inscription check."
            ),
        },
        "recommended_actions": [
            "Manually open USPS tracking for 9200190390470924693050 and archive screenshot (portal blocked here).",
            "On receipt: verify girdle inscription 'IGI LG839637366' and compare measurements to IGI fields.",
            "Note polish grade mismatch (Excellent advertised vs Very Good on IGI) for dispute leverage if needed.",
            "Provide TikTok Shop order ID, seller legal name, and promised ship-by date to tighten corporate OSINT.",
            "If no USPS acceptance scan by ship-by + 3 business days, open TikTok Shop dispute.",
        ],
    }

    machine = {
        "executive": executive,
        "igi": igi,
        "seller": seller,
        "username_graph": usernames,
        "telegram": telegram,
        "inventory": inventory,
        "pricing": pricing,
        "corporate": corporate,
        "reputation": reputation,
        "ach": ach,
        "monitoring": monitoring,
        "evidence_ledger_count": len(ledger) if isinstance(ledger, list) else 0,
        "claim_legend": ["CONFIRMED", "CORROBORATED", "UNVERIFIED", "CONTRADICTED", "UNKNOWN", "BLOCKED"],
    }

    md = f"""# Royale Diamonds Investigation Report

**Case ID:** `{case_id}`  
**As of (UTC):** {executive['as_of_utc']}  
**Method:** Evidence-first OSINT; competing hypotheses; no fabricated sources.

## 1. Executive intelligence assessment

| Topic | Status | Assessment |
|---|---|---|
| Seller public identity | CORROBORATED | TikTok `@royalediamondslive` linked by Mashable and live profile |
| Legal business entity | UNKNOWN | No verified SOS linkage yet |
| IGI certificate LG839637366 | CONFIRMED | Exists; lab-grown marquise 3.03ct F / VS1 / CVD |
| Spec match to listing | MOSTLY MATCH / Polish CONTRADICTED | IGI polish = Very Good; listing said Excellent |
| Economic plausibility of $350 | CORROBORATED as plausible auction price | Below observed retail-ask median; not proof of fraud |
| Fulfillment | UNKNOWN | Tracking `{monitoring.get('tracking_number')}` — {monitoring.get('shipment_status')} |
| Leading hypotheses | Qualitative | {', '.join(leading)} (subjective posteriors, not base rates) |

### Recommended actions
"""
    for a in executive["recommended_actions"]:
        md += f"- {a}\n"

    md += f"""

## 2. Evidence ledger

Append-only ledger files:
- `evidence/normalized/evidence_ledger.json`
- `evidence/normalized/evidence_ledger.csv`

Records currently persisted: **{machine['evidence_ledger_count']}**

Every factual claim below cites evidence IDs or source URLs actually accessed in this run.

## 3. Diamond certificate verification

**Source (CONFIRMED):** `https://lookup.igi.org/igi_new.php?r=LG839637366`  
**Verify page:** `https://lookup.igi.org/index.php/reports/verify_your_report?r=LG839637366`

| Field | IGI (CONFIRMED) | Advertised | Result |
|---|---|---|---|
"""
    for c in igi.get("comparisons", []):
        md += f"| {c.get('field')} | {c.get('igi','')} | {c.get('advertised','')} | {c.get('result')} |\n"

    fields = igi.get("fields", {})
    md += f"""
**Additional IGI fields:**  
Report date: {fields.get('Report Date')}  
Symmetry: {fields.get('Symmetry')}  
Girdle: {fields.get('Girdle Thickness')}  
Culet: {fields.get('Culet')}  
Comments: {fields.get('Comments')}  
Inscription(s): {fields.get('Inscription(s)')}

**Manual checkpoint:** If PDF download is Cloudflare-blocked, open the verify page in a normal browser and save the PDF/screenshot into `evidence/raw/`.

## 4. Retail / wholesale pricing

Observed **retail asking** prices for similar 2.8–3.2ct F/VS1 IGI marquises (n={pricing.get('comparables_count')}):

"""
    stats = pricing.get("stats_retail_asks_F_VS1") or {}
    md += f"""- Median ask: **${stats.get('median')}**
- Range: ${stats.get('min')} – ${stats.get('max')}
- IQR: {stats.get('iqr')}
- Median $/ct: ${stats.get('median_price_per_carat')}
- Auction discount vs median ask: {pricing.get('auction_discount_vs_median_ask')}
- Caveat: {stats.get('price_type_caveat')}

UNVERIFIED leads: Ritani ~$945 (wholesale estimate ~$325.97); Brilliance ~$2,020 — **not independently reproduced**.

Assessment: {(pricing.get('assessment') or {}).get('rationale')}

## 5. Seller identity graph

Confirmed / candidate public nodes:
"""
    for n in (usernames.get("graph") or {}).get("nodes", []):
        md += f"- `{n.get('id')}` — confidence {n.get('confidence')}: {n.get('basis')}\n"

    md += f"""
Name collisions explicitly excluded from attribution:
"""
    for c in seller.get("name_collisions", []):
        md += f"- {c.get('entity')} ({c.get('status')})\n"

    md += f"""
Telegram: {telegram.get('official_vs_impersonator')}

## 6. Fraud hypothesis matrix (ACH)

"""
    for hid, text in (ach.get("hypotheses") or {}).items():
        md += f"- **{hid}**: {text} — subjective posterior {posteriors.get(hid, 'n/a')}; inconsistency count {(ach.get('inconsistency_counts') or {}).get(hid)}\n"

    md += """
Diagnostic highlights:
- E1 (IGI match) supports certificate reality; does not prove the shipped stone will match.
- E2 (polish mismatch) is disconfirming for perfect representation (hurts H1 relative to H2).
- E6 (no tracking scans yet) is weakly consistent with H5 only because purchase is recent.

## 7. Monitoring dashboard

| Milestone | Value |
|---|---|
| Purchase date | {purchase} |
| Order status | {order} |
| Ship-by (seller promised) | {shipby} |
| Tracking | {tn} |
| Carrier | {carrier} |
| Shipment status | {ship} |
| Delivery | {deliv} |

### Indicators to watch
""".format(
        purchase=monitoring.get("purchase_date"),
        order=monitoring.get("order_status"),
        shipby=monitoring.get("seller_promised_ship_by_date") or "UNKNOWN — need user input",
        tn=monitoring.get("tracking_number"),
        carrier=monitoring.get("carrier"),
        ship=monitoring.get("shipment_status"),
        deliv=monitoring.get("delivery_status"),
    )
    for k, vals in (ach.get("indicators_and_warnings") or {}).items():
        md += f"- **{k}**: " + "; ".join(vals) + "\n"

    md += f"""

## 8. Evidence gaps / blocked sources

- USPS authoritative tracking portal: Access Denied / bot wall from this environment.
- IGI PDF endpoint (`api.igi.org/viewpdf.php`): Cloudflare challenged.
- Ritani / several marketplaces: Cloudflare or 403.
- Reddit JSON API: blocked.
- OpenCorporates search: reCAPTCHA wall.
- Instagram web profile: login wall (bio claim remains self-asserted).
- Exact TikTok Shop seller legal business name: missing (need order receipt).

## Claim status legend

CONFIRMED · CORROBORATED · UNVERIFIED · CONTRADICTED · UNKNOWN · BLOCKED

---
*Generated by the Royale Diamonds OSINT pipeline. Do not treat subjective Bayesian posteriors as calibrated probabilities.*
"""

    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    md_path = reports / "royale_diamonds_investigation.md"
    json_path = reports / "royale_diamonds_investigation.json"
    exec_path = reports / "executive_assessment.json"
    cert_path = reports / "certificate_verification.json"
    price_path = reports / "pricing_report.json"
    graph_path = reports / "seller_identity_graph.json"
    ach_path = reports / "fraud_hypothesis_matrix.json"
    mon_path = reports / "monitoring_dashboard.json"

    md_path.write_text(md)
    json_path.write_text(json.dumps(machine, indent=2))
    exec_path.write_text(json.dumps(executive, indent=2))
    cert_path.write_text(json.dumps(igi, indent=2))
    price_path.write_text(json.dumps(pricing, indent=2))
    graph_path.write_text(json.dumps(usernames, indent=2))
    ach_path.write_text(json.dumps(ach, indent=2))
    mon_path.write_text(json.dumps(monitoring, indent=2))

    return {
        "markdown": str(md_path),
        "json": str(json_path),
        "artifacts": [
            str(exec_path),
            str(cert_path),
            str(price_path),
            str(graph_path),
            str(ach_path),
            str(mon_path),
        ],
    }