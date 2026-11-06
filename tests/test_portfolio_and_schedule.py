from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from silent_stocks.config import Settings
from silent_stocks.portfolio_risk import APPROVAL, assess, propose
from silent_stocks.scheduler import build_trigger

PKG = Path(__file__).resolve().parent.parent / "silent_stocks"


def snapshot():
    bench = [100 + i for i in range(12)]
    return {"positions": {"option_level": None, "portfolio": {"total_value": 1000.0, "cash": 0.0, "crypto_value": 0.0},
                          "benchmark": {"price": 112, "monthly_closes": bench},
                          "holdings": [
                              {"symbol": "BIG", "quantity": 50, "price": 10.0, "monthly_closes": [8 + 0.2 * i for i in range(12)]},
                              {"symbol": "LEV", "quantity": 10, "price": 10.0, "leverage": 2.0, "asset_type": "leveraged_etf",
                               "monthly_closes": [10, 14, 8, 15, 7, 13, 9, 16, 8, 12, 9, 11]},
                              {"symbol": "IDX", "quantity": 4, "price": 100.0, "asset_type": "index_etf", "monthly_closes": bench}]}}


def test_concentration_and_leverage_trims_are_proposals_only():
    props = propose(assess(snapshot()))
    by = {p["symbol"]: p for p in props}
    assert by["BIG"]["side"] == "sell" and by["BIG"]["to_weight"] == 0.08
    assert by["LEV"]["to_weight"] == 0.03
    assert "IDX" in by and by["IDX"]["to_weight"] == 0.18
    for p in props:
        if p["side"] in ("buy", "sell"):
            assert p["status"] == APPROVAL
            assert p["review_equity_order"]["type"] == "market"


def test_no_buys_without_qualified_research():
    props = propose(assess(snapshot()), reports={})
    assert not [p for p in props if p["side"] == "buy" and p["kind"] == "research_buy"]
    assert any(p["kind"] == "no_buy" for p in props)


def _report(vetoes: list[str]):
    from types import SimpleNamespace
    return SimpleNamespace(status=SimpleNamespace(value="DISQUALIFIED"),
                           vetoes=[SimpleNamespace(code=c, severity="critical") for c in vetoes])


def test_veto_trims_need_complete_fundamentals():
    snap = snapshot()
    snap["positions"]["holdings"][0]["quantity"] = 5
    trimmed = {p["symbol"] for p in propose(assess(snap, reports={"BIG": _report(["SEVERE_DILUTION"])})) if p["side"] == "sell"}
    assert "BIG" in trimmed
    risk = assess(snap, reports={"BIG": _report(["MISSING_FUNDAMENTALS", "SEVERE_DILUTION"])})
    assert "BIG" not in {p["symbol"] for p in propose(risk) if p["side"] == "sell"}
    assert any(f["flag"] == "veto_needs_review" and f["symbol"] == "BIG" for f in risk["flags"])


def test_package_never_places_orders():
    for f in PKG.rglob("*.py"):
        tree = ast.parse(f.read_text())
        names = {n.attr if isinstance(n, ast.Attribute) else getattr(n, "id", None) for n in ast.walk(tree)}
        strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert "place_equity_order" not in names, f
        assert not any(s == "place_equity_order" for s in strings), f


def test_scheduler_fires_at_9am_new_york():
    trig = build_trigger(Settings())
    tz = ZoneInfo("America/New_York")
    nxt = trig.get_next_fire_time(None, datetime(2026, 11, 6, 10, 0, tzinfo=tz))
    assert (nxt.hour, nxt.minute, nxt.weekday()) == (9, 0, 0)
    assert nxt.utcoffset().total_seconds() == -5 * 3600
