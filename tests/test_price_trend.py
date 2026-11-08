from datetime import datetime
from zoneinfo import ZoneInfo

from silent_stocks.config import Settings
from silent_stocks.price_trend import _blank_state, apply_prints, trend_label
from silent_stocks.refresh import refresh_plan


def _print(day: str, price: float) -> dict:
    return {"price": price, "price_time": f"{day}T21:00:00Z"}


def test_drastic_move_alerts_once():
    state = _blank_state()
    rows, alerts = apply_prints(state, {"GS": [_print("2026-11-05", 100), _print("2026-11-06", 106)]})
    assert len(alerts) == 1
    assert alerts[0]["kind"] == "price_move"
    assert "not a research buy" in alerts[0]["message"]
    assert next(r for r in rows if r["symbol"] == "GS")["drastic"] is True
    _, again = apply_prints(state, {"GS": [_print("2026-11-06", 106)]})
    assert again == []


def test_small_move_is_recorded_without_an_alert():
    state = _blank_state()
    rows, alerts = apply_prints(state, {"KR": [_print("2026-11-05", 69.43), _print("2026-11-06", 67.71)]})
    assert alerts == []
    row = next(r for r in rows if r["symbol"] == "KR")
    assert row["drastic"] is False
    assert row["trend"] == "falling"
    assert abs(row["change_pct"] - (67.71 / 69.43 - 1)) < 1e-6


def test_missing_quote_stays_blank():
    rows, alerts = apply_prints(_blank_state(), {})
    lumi = next(r for r in rows if r["symbol"] == "LUMI")
    assert lumi["price"] is None
    assert lumi["trend"] == "baseline"
    assert alerts == []


def test_trend_label_needs_a_two_percent_net_move():
    flat = [{"price": 100}, {"price": 100.5}]
    rising = [{"price": 100}, {"price": 103}, {"price": 106}]
    assert trend_label(flat) == "flat"
    assert trend_label(rising) == "rising"


def test_refresh_plan_includes_tracked_symbols():
    syms = refresh_plan(Settings(), holdings=["AMD"], as_of=datetime(2026, 11, 8, tzinfo=ZoneInfo("America/New_York")).date())
    assert "GS" in syms["symbols"] and "LUMI" in syms["symbols"] and "KR" in syms["symbols"]
