"""Fraud complaint and reputation classification."""

from __future__ import annotations

import json
from pathlib import Path

from src.evidence_ledger import EvidenceLedger
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now


def analyze_reputation(ledger: EvidenceLedger | None = None) -> dict:
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "complaints"
    out_dir.mkdir(parents=True, exist_ok=True)

    findings = [
        {
            "id": "reddit_2026-08-23_overpay",
            "source": "https://www.reddit.com/r/labdiamond/comments/1vwjjf6/7ct_emerald_cut_f_vvs2/",
            "date": "2026-08-23",
            "classification": "unverified_allegation_mixed_with_positive_legit_opinion",
            "summary": (
                "Buyer asked if Royale Diamonds TikTok purchase was a scam after paying $1500. "
                "Commenters generally said likely legit but overpriced; one awaited delivery confirmation."
            ),
            "category": 4,  # unverified allegation / community discussion
            "independent_complaint": False,
            "notes": "Reddit JSON API blocked from this environment; content from search snippets + prior public discussion.",
        },
        {
            "id": "mashable_2026_coverage",
            "source": "https://mashable.com/life/tiktok-shop-lab-grown-diamond-live-auctions",
            "date": "2026-08",
            "classification": "positive_customer_experience_secondary",
            "summary": (
                "Buyers quoted as receiving IGI reports with purchases; describes high-pressure auctions "
                "and final-sale terms rather than non-delivery fraud."
            ),
            "category": 5,
            "independent_complaint": False,
        },
        {
            "id": "bbb_tiktok_jewelry_unrelated",
            "source": "https://nationaljeweler.com/articles/12338-better-business-bureau-warns-of-tiktok-jewelry-scam",
            "date": None,
            "classification": "irrelevant_name_collision_or_unrelated_scam",
            "summary": "BBB warning about TruGala-style discount-code jewelry scam — not Royale Diamonds.",
            "category": 6,
            "independent_complaint": False,
        },
        {
            "id": "pune_store_reviews",
            "source": "https://www.royalediamonds.com/",
            "date": "2025",
            "classification": "irrelevant_name_collision",
            "summary": "Negative Google-style reviews for a Pune jewelry store sharing the name.",
            "category": 6,
            "independent_complaint": False,
        },
    ]

    result = {
        "search_variations_used": [
            "Royale Diamonds fake diamond",
            "Royale Diamonds IGI fake",
            "Royale Diamonds chargeback",
            "Royale Diamonds never shipped",
            "Royale Diamonds wrong stone",
            "Royale Diamonds TikTok auction",
            "Royale Diamonds refund denied",
        ],
        "findings": findings,
        "pattern_assessment": (
            "Dominant public pattern is overpayment / auction psychology risk, not a corroborated "
            "non-fulfillment ring. No verified enforcement action against @royalediamondslive found."
        ),
        "counts": {
            "verified_official_enforcement": 0,
            "documented_customer_dispute": 0,
            "independently_corroborated_complaint": 0,
            "unverified_allegation": 1,
            "positive_customer_experience": 1,
            "irrelevant_name_collision": 2,
        },
        "collected_at_utc": utc_now().isoformat(),
    }
    (out_dir / "reputation_analysis.json").write_text(json.dumps(result, indent=2))
    ledger.append(
        EvidenceRecord(
            evidence_id="reputation_summary",
            source_url="local://reputation_analysis",
            source_title="Reputation and complaints synthesis",
            source_category="complaints",
            reliability=Reliability.C,
            evidence_tier=EvidenceTier.SECONDARY,
            status=ClaimStatus.UNVERIFIED,
            extracted_facts=result["counts"],
        )
    )
    return result