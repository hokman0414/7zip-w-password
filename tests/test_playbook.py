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


FILLED = "2026-11-20T17:29:35Z"
FRIDAY_TRIMS = [
    {"symbol": "CIFR", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 5.505, "filled_at": FILLED},
    {"symbol": "NBIS", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 84.2158, "filled_at": FILLED},
    {"symbol": "IREN", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 12.405, "filled_at": FILLED},
    {"symbol": "DRAM", "side": "sell", "verb": "trim", "rule": "trim_thesis_fails", "fill_price": 34.3618, "filled_at": FILLED},
]
WEDNESDAY = datetime(2026, 11, 25, 17, tzinfo=timezone.utc)


def test_one_name_does_not_move_the_shared_fraction():
    rules = json_copy(DEFAULT_RULES)
    prices = {"CIFR": 5.84, "NBIS": 87.11, "IREN": 12.55, "DRAM": 35.36}
    updated = learn_from_fills(rules, FRIDAY_TRIMS, prices, WEDNESDAY)
    assert updated["fractions"]["trim_thesis_fails"] == 0.5
    assert "stays 0.50" in updated["gaps"][-1]["gap"]


def test_a_drop_after_the_trim_raises_the_next_fraction():
    rules = json_copy(DEFAULT_RULES)
    updated = learn_from_fills(rules, FRIDAY_TRIMS[1:2], {"NBIS": 70.0}, WEDNESDAY)
    assert updated["fractions"]["trim_thesis_fails"] == 0.75
    assert "NBIS" in updated["gaps"][-1]["gap"]
    assert rules["fractions"]["trim_thesis_fails"] == 0.5


def test_a_one_session_bounce_does_not_move_the_fraction():
    rules = json_copy(DEFAULT_RULES)
    monday_prices = {"CIFR": 6.22, "NBIS": 97.11, "IREN": 14.55, "DRAM": 39.48}
    updated = learn_from_fills(rules, FRIDAY_TRIMS, monday_prices, datetime(2026, 11, 23, 20, tzinfo=timezone.utc))
    assert updated["fractions"]["trim_thesis_fails"] == 0.5
    assert updated["learned"] == []


def test_a_batch_is_scored_once():
    rules = json_copy(DEFAULT_RULES)
    falling = {"CIFR": 4.9, "NBIS": 75.0, "IREN": 11.0, "DRAM": 30.0}
    once = learn_from_fills(rules, FRIDAY_TRIMS, falling, WEDNESDAY)
    twice = learn_from_fills(once, FRIDAY_TRIMS, falling, datetime(2026, 11, 30, 17, tzinfo=timezone.utc))
    assert once["fractions"]["trim_thesis_fails"] == 0.75
    assert twice["fractions"]["trim_thesis_fails"] == 0.75
    assert once["learned"] == ["trim_thesis_fails:2026-11-20"]


def json_copy(value):
    import json
    return json.loads(json.dumps(value))
