from datetime import datetime, timezone

from silent_stocks.playbook import DEFAULT_RULES, learn_from_fills, parse_request, size_request

FRIDAY = """
WDC, SNDK, DRAM Review / trim Heavy exposure to memory and storage cycles
NBIS, WULF, CIFR, IREN Trim first High-risk AI infrastructure and crypto-related exposure
BITU Exit candidate Daily 2x Bitcoin leverage
"""


def test_friday_request_parses_exit_trim_and_review():
    verbs = {(i["symbol"], i["verb"]) for i in parse_request(FRIDAY)}
    assert ("BITU", "exit") in verbs
    assert ("NBIS", "trim") in verbs and ("WULF", "trim") in verbs
    assert ("DRAM", "trim") in verbs
    assert ("WDC", "trim") in verbs
    assert ("AI", "trim") not in verbs


def test_exit_sells_the_position_and_a_failed_thesis_trims_half():
    holdings = [
        {"symbol": "BITU", "available": 17.950369, "price": 7.285, "asset_type": "leveraged_etf"},
        {"symbol": "NBIS", "available": 0.794992, "price": 84.2158},
        {"symbol": "NFLX", "available": 2.0, "price": 60.0},
        {"symbol": "DRAM", "available": 2.392945, "price": 34.365},
    ]
    sat = {
        "BITU": {"leading": "H4", "red_team_survives": False, "leveraged": True},
        "NBIS": {"leading": "H4", "red_team_survives": False},
        "NFLX": {"leading": "H1", "red_team_survives": True},
    }
    intents = [
        {"symbol": "BITU", "verb": "exit", "theme": "2x bitcoin"},
        {"symbol": "NBIS", "verb": "trim", "theme": "ai infra"},
        {"symbol": "NFLX", "verb": "trim", "theme": "thesis holds"},
        {"symbol": "WULF", "verb": "trim", "theme": "not held"},
        {"symbol": "DRAM", "verb": "review", "theme": "review only"},
    ]
    result = size_request(intents, holdings, sat, DEFAULT_RULES)
    by = {o["symbol"]: o for o in result["orders"]}
    assert by["BITU"]["quantity"] == "17.950369" and by["BITU"]["rule"] == "exit"
    assert by["NBIS"]["fraction"] == 0.5
    assert by["NFLX"]["fraction"] == 0.25
    assert "WULF trim: not held" in result["notes"]
    assert "DRAM review: review only, no order" in result["notes"]


def test_a_trim_with_no_report_is_unconfirmed_and_uses_half():
    holdings = [{"symbol": "DRAM", "available": 2.392945, "price": 34.365}]
    result = size_request([{"symbol": "DRAM", "verb": "trim", "theme": "memory"}], holdings, {}, DEFAULT_RULES)
    order = result["orders"][0]
    assert order["fraction"] == 0.5
    assert order["rule"] == "trim_thesis_fails"
    assert "unconfirmed" in order["rationale"]


def test_one_name_does_not_move_the_shared_fraction():
    rules = json_copy(DEFAULT_RULES)
    fills = [
        {"symbol": "CIFR", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 5.505},
        {"symbol": "NBIS", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 84.2158},
        {"symbol": "IREN", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 12.405},
        {"symbol": "DRAM", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 34.3618},
    ]
    prices = {"CIFR": 5.84, "NBIS": 87.11, "IREN": 12.55, "DRAM": 35.36}
    updated = learn_from_fills(rules, fills, prices, datetime(2026, 11, 22, tzinfo=timezone.utc))
    assert updated["fractions"]["trim_thesis_fails"] == 0.5
    assert "stays 0.50" in updated["gaps"][-1]["gap"]


def test_a_drop_after_the_trim_raises_the_next_fraction():
    rules = json_copy(DEFAULT_RULES)
    updated = learn_from_fills(rules, [{
        "symbol": "NBIS", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 84.2158,
    }], {"NBIS": 70.0}, datetime(2026, 11, 23, tzinfo=timezone.utc))
    assert updated["fractions"]["trim_thesis_fails"] == 0.75
    assert "NBIS" in updated["gaps"][-1]["gap"]
    assert rules["fractions"]["trim_thesis_fails"] == 0.5


def json_copy(value):
    import json
    return json.loads(json.dumps(value))
