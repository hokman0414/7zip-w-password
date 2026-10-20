from src.ach_analysis import build_ach
from src.monitoring import classify_usps_number
from src.pricing_analysis import analyze_pricing


def test_pricing_has_at_least_10_comps():
    result = analyze_pricing(350)
    assert result["comparables_count"] >= 8
    assert result["stats_retail_asks_F_VS1"]["median"] is not None
    assert result["assessment"]["economically_plausible"] is True


def test_usps_format():
    assert classify_usps_number("9200190390470924693050")["format_looks_like_usps"] is True
    assert classify_usps_number("not-a-tracking")["format_looks_like_usps"] is False


def test_ach_ranks_without_crash():
    ach = build_ach(
        {
            "igi": {
                "verification_status": "CONFIRMED",
                "comparisons": [{"field": "polish", "result": "MISMATCH"}],
            },
            "seller": {"confirmed_username": "royalediamondslive"},
            "pricing": {
                "target": {"purchase_price_usd": 350},
                "stats_retail_asks_F_VS1": {"median": 900},
            },
            "tracking": {"status": "NO_INFO"},
            "inventory": {},
        }
    )
    assert "H1" in ach["hypotheses"]
    assert ach["current_leading_hypotheses"]
    assert sum(ach["subjective_bayes"]["posteriors"].values()) > 0.99