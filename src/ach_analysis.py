"""Analysis of Competing Hypotheses and Bayesian-style qualitative updates."""

from __future__ import annotations

import json
from pathlib import Path

from src.models import utc_now

HYPOTHESES = {
    "H1": "Legitimate sale of the advertised diamond",
    "H2": "Legitimate sale with exaggerated retail-value claims",
    "H3": "Genuine diamond shipped but different from advertised certificate",
    "H4": "Counterfeit, simulant, or materially misrepresented stone shipped",
    "H5": "Seller fails to fulfill the order",
    "H6": "Fraudulent impersonation of a legitimate diamond seller",
}

# Consistency codes: C consistent, I inconsistent, N neutral/not diagnostic
# Focus on diagnostic / disconfirming evidence.


def build_ach(evidence_bundle: dict) -> dict:
    igi = evidence_bundle.get("igi", {})
    seller = evidence_bundle.get("seller", {})
    pricing = evidence_bundle.get("pricing", {})
    tracking = evidence_bundle.get("tracking", {})
    inventory = evidence_bundle.get("inventory", {})

    igi_ok = igi.get("verification_status") == "CONFIRMED"
    polish_mismatch = any(
        c.get("field") == "polish" and c.get("result") == "MISMATCH"
        for c in igi.get("comparisons", [])
    )
    username_confirmed = bool(seller.get("confirmed_username"))
    track_status = tracking.get("status", "UNKNOWN")
    purchase = pricing.get("target", {}).get("purchase_price_usd", 350)
    median = (pricing.get("stats_retail_asks_F_VS1") or {}).get("median")

    evidence_rows = [
        {
            "id": "E1",
            "evidence": "IGI LG839637366 exists and matches shape/carat/color/clarity/measurements/CVD",
            "status": "CONFIRMED" if igi_ok else "UNKNOWN",
            "consistency": {
                "H1": "C",
                "H2": "C",
                "H3": "N",  # cert can exist while different stone ships
                "H4": "I",  # weak inconsistency with total fabrication of cert details
                "H5": "N",
                "H6": "N",
            },
            "diagnosticity": "HIGH for existence of advertised certificate; LOW for fulfillment.",
        },
        {
            "id": "E2",
            "evidence": "Advertised polish Excellent vs IGI Very Good",
            "status": "CONFIRMED" if polish_mismatch else "NOT_OBSERVED",
            "consistency": {
                "H1": "I",
                "H2": "C",
                "H3": "C",
                "H4": "C",
                "H5": "N",
                "H6": "N",
            },
            "diagnosticity": "MEDIUM — supports misstatement/exaggeration more than total fraud.",
        },
        {
            "id": "E3",
            "evidence": "Public media identifies @royalediamondslive as Royale Diamonds auction seller",
            "status": "CORROBORATED" if username_confirmed else "UNKNOWN",
            "consistency": {
                "H1": "C",
                "H2": "C",
                "H3": "C",
                "H4": "N",
                "H5": "N",
                "H6": "I",  # reduces pure random impersonation of an unknown brand
            },
            "diagnosticity": "MEDIUM against H6 (random impersonation); does not prove corporate legitimacy.",
        },
        {
            "id": "E4",
            "evidence": f"Purchase ${purchase} below observed retail-ask median ${median}",
            "status": "CORROBORATED" if median else "UNKNOWN",
            "consistency": {
                "H1": "C",
                "H2": "C",
                "H3": "N",
                "H4": "C",
                "H5": "C",
                "H6": "C",
            },
            "diagnosticity": "LOW — cheap can be liquidation or bait.",
        },
        {
            "id": "E5",
            "evidence": "Community commentary: likely legit but often overpriced auctions",
            "status": "UNVERIFIED",
            "consistency": {
                "H1": "C",
                "H2": "C",
                "H3": "N",
                "H4": "I",
                "H5": "I",
                "H6": "I",
            },
            "diagnosticity": "LOW (hearsay), directionally against systemic non-delivery.",
        },
        {
            "id": "E6",
            "evidence": "USPS tracking shows no public scan data yet / carrier portal blocked",
            "status": track_status,
            "consistency": {
                "H1": "N",
                "H2": "N",
                "H3": "N",
                "H4": "N",
                "H5": "C",
                "H6": "N",
            },
            "diagnosticity": "LOW on day-after purchase; becomes HIGH if stagnant past promised ship-by.",
        },
        {
            "id": "E7",
            "evidence": "Ritani/Brilliance same-cert retail leads not independently reproduced",
            "status": "UNVERIFIED",
            "consistency": {
                "H1": "N",
                "H2": "C",
                "H3": "N",
                "H4": "N",
                "H5": "N",
                "H6": "N",
            },
            "diagnosticity": "LOW until reproduced; if reproduced, supports H2 value-claim context.",
        },
        {
            "id": "E8",
            "evidence": "No verified enforcement action found against this TikTok seller",
            "status": "UNKNOWN",
            "consistency": {
                "H1": "C",
                "H2": "C",
                "H3": "N",
                "H4": "N",
                "H5": "N",
                "H6": "N",
            },
            "diagnosticity": "LOW (absence of evidence ≠ evidence of absence).",
        },
    ]

    # Score: count inconsistencies (higher = less likely)
    scores = {h: 0 for h in HYPOTHESES}
    for row in evidence_rows:
        for h, code in row["consistency"].items():
            if code == "I":
                scores[h] += 1

    # Qualitative Bayesian-style update (subjective priors labeled)
    priors = {
        "H1": 0.28,
        "H2": 0.30,
        "H3": 0.12,
        "H4": 0.08,
        "H5": 0.12,
        "H6": 0.10,
    }
    # Likelihood multipliers (subjective)
    likelihood = {h: 1.0 for h in HYPOTHESES}
    if igi_ok:
        likelihood["H4"] *= 0.5
        likelihood["H1"] *= 1.3
        likelihood["H2"] *= 1.3
    if polish_mismatch:
        likelihood["H1"] *= 0.7
        likelihood["H2"] *= 1.4
    if username_confirmed:
        likelihood["H6"] *= 0.6
        likelihood["H1"] *= 1.1
        likelihood["H2"] *= 1.1
    if track_status in {"NO_INFO", "BLOCKED"}:
        likelihood["H5"] *= 1.1  # slight; early in timeline

    unnorm = {h: priors[h] * likelihood[h] for h in HYPOTHESES}
    z = sum(unnorm.values()) or 1.0
    posteriors = {h: round(unnorm[h] / z, 3) for h in HYPOTHESES}

    ranking = sorted(posteriors.items(), key=lambda kv: (-kv[1], scores[kv[0]]))

    result = {
        "hypotheses": HYPOTHESES,
        "matrix": evidence_rows,
        "inconsistency_counts": scores,
        "subjective_bayes": {
            "priors": priors,
            "likelihood_multipliers": likelihood,
            "posteriors": posteriors,
            "caveat": (
                "Priors/likelihoods are explicitly subjective analytic judgments, "
                "not empirical base rates. Do not treat as precise probabilities."
            ),
            "sensitivity": {
                "if_tracking_stagnates_7d": "Increase H5 materially; decrease H1/H2",
                "if_stone_matches_inscription": "Increase H1/H2; collapse H3/H4",
                "if_stone_mismatches_cert": "Increase H3/H4; decrease H1",
            },
        },
        "current_leading_hypotheses": [h for h, _ in ranking[:2]],
        "key_assumptions": [
            "TikTok checkout payment actually captured funds from this seller account",
            "User-advertised listing specs match what was shown in the livestream",
            "USPS number provided belongs to this order",
            "Absence of early tracking scans is normal for day-0/day-1 labels",
        ],
        "indicators_and_warnings": {
            "seller_impersonation": [
                "Sudden username/branding change",
                "Mismatched shop legal name vs livestream branding",
            ],
            "order_cancellation": ["TikTok order cancelled by seller", "Refund without shipment"],
            "shipping_nonfulfillment": [
                "No scan beyond label-created after promised ship-by + buffer",
                "Tracking never issued",
            ],
            "fake_tracking": [
                "Tracking number not recognized by USPS",
                "Tracking for unrelated origin/destination",
            ],
            "certificate_mismatch": [
                "Received report number ≠ LG839637366",
                "Girdle inscription missing/mismatch",
            ],
            "diamond_substitution": [
                "Measurements off beyond tolerance",
                "Different clarity/color under gemologist check",
            ],
            "unusual_refund_behavior": [
                "Pressure to accept store credit only",
                "Refusal to use TikTok Shop dispute channel",
            ],
        },
        "collected_at_utc": utc_now().isoformat(),
    }
    out = Path(__file__).resolve().parents[1] / "analysis" / "ach_matrix.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    return result