from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from silent_stocks.config import Settings
from silent_stocks.execution import ACCOUNT_PLACEHOLDER, AutotradeConfig, load_state, plan_orders, record_executions
from silent_stocks.refresh import validate_portfolio

ET = ZoneInfo("America/New_York")
MONDAY_10 = datetime(2026, 11, 9, 10, 0, tzinfo=ET).astimezone(timezone.utc)


@pytest.fixture
def settings(tmp_path):
    return replace(Settings(), data_dir=tmp_path, db_path=tmp_path / "t.db", reports_dir=tmp_path / "r")


@pytest.fixture
def armed_env(monkeypatch):
    monkeypatch.setenv("ROBINHOOD_AGENTIC_ACCOUNT", "999990643")
    monkeypatch.delenv("SILENT_STOP", raising=False)


def cfg(**kw):
    base = dict(enabled=True, account_last4="0643", allowed_kinds=["risk_trim", "hedge", "research_buy", "core_reinvest"],
                max_order_usd=400, max_daily_turnover_pct=0.2, max_orders_per_day=6, cash_reserve_pct=0.05)
    return AutotradeConfig(**(base | kw))


def doc(cash=0.0, captured=MONDAY_10 - timedelta(minutes=10), total=1000.0):
    return {"captured_at": captured.isoformat(), "positions": {
        "portfolio": {"total_value": total, "equity_value": total - cash, "cash": cash, "buying_power": cash},
        "benchmark": {"price": 1, "monthly_closes": [1] * 12},
        "holdings": [{"symbol": "AAA", "quantity": 10, "available": 8, "price": 50.0, "monthly_closes": [50] * 12},
                     {"symbol": "BBB", "quantity": 10, "available": 10, "price": 50.0, "monthly_closes": [50] * 12}]}}


SELL = {"symbol": "AAA", "side": "sell", "quantity": 9.0, "kind": "risk_trim", "rationale": "r"}
BUY = {"symbol": "SPY", "side": "buy", "dollar_amount": 300.0, "kind": "core_reinvest", "rationale": "r"}


def test_armed_plan_clips_to_available_and_caps(settings, armed_env):
    plan = plan_orders(cfg(max_order_usd=1000), settings, [SELL], doc(), [], MONDAY_10, load_state(settings))
    assert plan["armed"], plan["blocked_reasons"]
    o = plan["orders"][0]
    assert o["params"]["quantity"] == "4.000000"
    assert o["params"]["account_number"] == ACCOUNT_PLACEHOLDER
    assert o["clipped"] and o["ref_id"]


def test_turnover_cap_limits_total(settings, armed_env):
    plan = plan_orders(cfg(max_order_usd=1000, max_daily_turnover_pct=0.1), settings, [SELL], doc(), [], MONDAY_10, load_state(settings))
    assert plan["orders"][0]["est_usd"] == pytest.approx(100.0)


@pytest.mark.parametrize("mutate,reason", [
    (lambda s, c: c.__setattr__("enabled", False), "disabled"),
    (lambda s, c: (s.data_dir / "STOP_TRADING").write_text("x"), "kill switch"),
])
def test_disarm_paths(settings, armed_env, mutate, reason):
    c = cfg()
    mutate(settings, c)
    plan = plan_orders(c, settings, [SELL], doc(), [], MONDAY_10, load_state(settings))
    assert not plan["armed"] and plan["orders"] == [] and any(reason in r for r in plan["blocked_reasons"])
    assert plan["would_place_if_armed"]


def test_missing_or_wrong_account_blocks(settings, monkeypatch):
    monkeypatch.delenv("ROBINHOOD_AGENTIC_ACCOUNT", raising=False)
    assert not plan_orders(cfg(), settings, [SELL], doc(), [], MONDAY_10, load_state(settings))["armed"]
    monkeypatch.setenv("ROBINHOOD_AGENTIC_ACCOUNT", "123451111")
    assert not plan_orders(cfg(), settings, [SELL], doc(), [], MONDAY_10, load_state(settings))["armed"]


def test_weekend_holiday_and_window_block(settings, armed_env):
    sat = datetime(2026, 11, 7, 11, 0, tzinfo=ET).astimezone(timezone.utc)
    thanksgiving = datetime(2026, 11, 26, 11, 0, tzinfo=ET).astimezone(timezone.utc)
    early = datetime(2026, 11, 9, 9, 31, tzinfo=ET).astimezone(timezone.utc)
    for t in (sat, thanksgiving, early):
        assert not plan_orders(cfg(), settings, [SELL], doc(captured=t), [], t, load_state(settings))["armed"]


def test_stale_snapshot_and_validation_errors_block(settings, armed_env):
    assert not plan_orders(cfg(), settings, [SELL], doc(captured=MONDAY_10 - timedelta(hours=7)), [], MONDAY_10, load_state(settings))["armed"]
    assert not plan_orders(cfg(), settings, [SELL], doc(), ["bad"], MONDAY_10, load_state(settings))["armed"]


def test_buys_only_from_spendable_cash_above_reserve(settings, armed_env):
    plan = plan_orders(cfg(), settings, [BUY], doc(cash=0.0), [], MONDAY_10, load_state(settings))
    assert plan["orders"] == [] and "insufficient spendable cash" in plan["rejected"][0]["reason"]
    plan = plan_orders(cfg(), settings, [BUY], doc(cash=200.0), [], MONDAY_10, load_state(settings))
    assert plan["orders"][0]["params"]["dollar_amount"] == "150.00"


def test_disallowed_kind_rejected(settings, armed_env):
    plan = plan_orders(cfg(allowed_kinds=["risk_trim"]), settings, [BUY], doc(cash=500), [], MONDAY_10, load_state(settings))
    assert plan["orders"] == [] and "not in allowed_kinds" in plan["rejected"][0]["reason"]


def test_drawdown_halts_buys_then_everything(settings, armed_env):
    st = {"high_water_mark": 1250.0, "last_trades": {}}
    plan = plan_orders(cfg(), settings, [SELL, BUY], doc(cash=200), [], MONDAY_10, st)
    assert plan["buys_halted"] and [o["side"] for o in plan["orders"]] == ["sell"]
    st = {"high_water_mark": 2000.0, "last_trades": {}}
    assert not plan_orders(cfg(), settings, [SELL], doc(), [], MONDAY_10, st)["armed"]


def test_cooldown_and_record_roundtrip(settings, armed_env):
    record_executions(settings, [{"ref_id": "x", "symbol": "AAA", "side": "sell", "status": "placed"}], MONDAY_10 - timedelta(days=1), 1000.0)
    st = load_state(settings)
    assert st["high_water_mark"] == 1000.0 and "AAA" in st["last_trades"]
    plan = plan_orders(cfg(), settings, [SELL], doc(), [], MONDAY_10, st)
    assert plan["orders"] == [] and "cooldown" in plan["rejected"][0]["reason"]


def test_record_refuses_account_number(settings):
    with pytest.raises(ValueError):
        record_executions(settings, [{"ref_id": "x", "symbol": "A", "side": "sell", "status": "placed", "account_number": "1"}], MONDAY_10)


def test_ref_id_is_deterministic(settings, armed_env):
    a = plan_orders(cfg(), settings, [SELL], doc(), [], MONDAY_10, load_state(settings))["orders"][0]["ref_id"]
    b = plan_orders(cfg(), settings, [SELL], doc(), [], MONDAY_10 + timedelta(minutes=5), load_state(settings))["orders"][0]["ref_id"]
    assert a == b


def test_portfolio_validation_catches_transcription_error():
    d = doc()
    d["positions"]["portfolio"]["equity_value"] = 2000.0
    errors, _ = validate_portfolio(d, MONDAY_10)
    assert any("differs >3%" in e for e in errors)
