from __future__ import annotations

import pytest

from silent_stocks.valuation import ValuationInputs, implied_price, peer_median_excluding, value


def base(**kw):
    d = dict(ticker="T", price=10.0, market_cap=1000.0, shares_outstanding=100.0, cash=100.0, debt=50.0,
             revenue_ttm=500.0, revenue_growth=0.3, fcf_ttm=0.0, dilution_yoy=0.0, peer_ev_revenue_median=2.0)
    d.update(kw)
    return ValuationInputs(**d)


def test_enterprise_value_and_multiple():
    v = value(base(), mc_sims=1000)
    assert v.enterprise_value == pytest.approx(1000 + 50 - 100)
    assert v.ev_revenue == pytest.approx(950 / 500)
    assert v.net_debt == pytest.approx(-50)
    assert v.price_to_double == 20.0


def test_revenue_required_to_double():
    v = value(base(), mc_sims=1000)
    ev_target = 2 * 1000 + 50 - 100
    assert v.revenue_required_to_double_at_current_multiple == pytest.approx(ev_target / 1.9)
    assert v.revenue_required_to_double_at_peer_multiple == pytest.approx(ev_target / 2.0)
    assert v.growth_required_to_double_at_current_multiple == pytest.approx(ev_target / 1.9 / 500 - 1)


def test_implied_price_arithmetic():
    p = implied_price(rev_ttm=500, growth=0.2, ev_rev=2.0, debt=50, cash=100, fcf=10, shares=100, dilution=0.1)
    assert p == pytest.approx((2.0 * 600 - 50 + 110) / 110)


def test_implied_price_floors_equity_at_zero():
    assert implied_price(100, -0.5, 0.1, 1000, 0, 0, 10, 0) == 0.0


def test_scenarios_ordered_and_reproducible():
    a, b = value(base(), seed=7), value(base(), seed=7)
    prices = {s.name: s.implied_price for s in a.scenarios}
    assert prices["bear"] < prices["base"] < prices["bull"]
    assert a.monte_carlo.p_double == b.monte_carlo.p_double
    assert all(s.probability is None for s in a.scenarios)


def test_bull_meets_double_flag_matches_price():
    v = value(base(), mc_sims=500)
    bull = next(s for s in v.scenarios if s.name == "bull")
    assert v.bull_meets_double == (bull.implied_price >= 20.0)


def test_missing_inputs_skip_valuation():
    v = value(base(cash=None), mc_sims=100)
    assert v.scenarios == [] and v.monte_carlo is None and v.bull_meets_double is None
    assert any("cash unavailable" in n for n in v.notes)


def test_peer_median_excludes_self_and_needs_three():
    data = {"A": ("s", 1.0), "B": ("s", 2.0), "C": ("s", 3.0), "D": ("s", 100.0), "E": ("x", 5.0)}
    assert peer_median_excluding("D", "s", data) == 2.0
    assert peer_median_excluding("A", "x", data) is None
