"""Valuation and forecast engine: bear/base/bull scenarios, required-to-double math, sensitivity and Monte Carlo.

All scenario inputs are explicit and derived mechanically from trailing evidence so they are reproducible. Scenario
probabilities are left unassigned (not calibrated). The Monte Carlo output is a statistical forecast under the
stated input distributions, not a calibrated probability.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt

import numpy as np

from .models import MonteCarloResult, Scenario, SensitivityCell, ValuationResult


@dataclass
class ValuationInputs:
    ticker: str
    price: float | None
    price_time: object = None
    market_cap: float | None = None
    shares_outstanding: float | None = None
    diluted_shares: float | None = None
    cash: float | None = None
    debt: float | None = None
    revenue_ttm: float | None = None
    revenue_growth: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    ebitda_ttm: float | None = None
    fcf_ttm: float | None = None
    net_income_ttm: float | None = None
    dilution_yoy: float | None = None
    backlog: float | None = None
    backlog_growth: float | None = None
    peer_ev_revenue_median: float | None = None
    peer_group: str | None = None
    volatility_annual: float | None = None
    return_12m: float | None = None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def scenario_assumptions(v: ValuationInputs, current_mult: float) -> dict[str, dict[str, float]]:
    g_hist = v.revenue_growth if v.revenue_growth is not None else 0.05
    # Growth decays toward the mean: base case keeps 75% of trailing growth, bounded.
    base_g = _clamp(0.75 * g_hist, -0.15, 0.80)
    spread = max(0.15, 0.5 * abs(base_g))
    peer = v.peer_ev_revenue_median or current_mult
    base_m = sqrt(current_mult * peer)
    bear_m = min(current_mult, peer) * 0.7
    bull_m = max(current_mult, peer) * 1.2
    dil = max(v.dilution_yoy or 0.0, 0.0)
    burning = (v.fcf_ttm or 0.0) < 0
    fcf = v.fcf_ttm or 0.0
    return {
        "bear": {"revenue_growth": base_g - spread, "ev_revenue": bear_m,
                 "dilution": min(max(dil, 0.10 if burning else 0.02), 0.6), "fcf": fcf - abs(fcf) * 0.2},
        "base": {"revenue_growth": base_g, "ev_revenue": base_m, "dilution": min(dil, 0.5), "fcf": fcf},
        "bull": {"revenue_growth": base_g + spread, "ev_revenue": bull_m, "dilution": dil * 0.5,
                 "fcf": fcf + abs(fcf) * 0.5},
    }


def implied_price(rev_ttm: float, growth: float, ev_rev: float, debt: float, cash: float, fcf: float,
                  shares: float, dilution: float) -> float | None:
    if shares <= 0:
        return None
    equity = ev_rev * rev_ttm * (1 + growth) - debt + max(cash + fcf, 0.0)
    return max(equity, 0.0) / (shares * (1 + dilution))


def value(v: ValuationInputs, mc_sims: int = 10000, seed: int = 42) -> ValuationResult:
    notes: list[str] = []
    shares = max(filter(None, [v.diluted_shares, v.shares_outstanding]), default=None)
    mcap = v.market_cap if v.market_cap else (v.price * shares if v.price and shares else None)
    cash, debt = v.cash, v.debt
    ev = mcap + (debt or 0.0) - (cash or 0.0) if mcap is not None and cash is not None else None
    if cash is None:
        notes.append("cash unavailable: enterprise value not computed")
    ev_rev = ev / v.revenue_ttm if ev is not None and v.revenue_ttm and v.revenue_ttm > 0 else None
    ev_ebitda = ev / v.ebitda_ttm if ev is not None and v.ebitda_ttm and v.ebitda_ttm > 0 else None
    pe = mcap / v.net_income_ttm if mcap and v.net_income_ttm and v.net_income_ttm > 0 else None
    price_to_double = 2 * v.price if v.price else None

    base = dict(
        ticker=v.ticker, price=v.price, price_time=v.price_time, market_cap=mcap,
        shares_outstanding=v.shares_outstanding, diluted_shares=shares, cash=cash, debt=debt,
        net_debt=(debt - cash) if debt is not None and cash is not None else None, enterprise_value=ev,
        revenue_ttm=v.revenue_ttm, revenue_growth_yoy=v.revenue_growth, gross_margin=v.gross_margin,
        operating_margin=v.operating_margin, ebitda_ttm=v.ebitda_ttm, fcf_ttm=v.fcf_ttm, backlog=v.backlog,
        backlog_growth_yoy=v.backlog_growth, ev_revenue=ev_rev, ev_ebitda=ev_ebitda, pe=pe,
        peer_ev_revenue_median=v.peer_ev_revenue_median, peer_group=v.peer_group, dilution_yoy=v.dilution_yoy,
        price_to_double=price_to_double, volatility_annual=v.volatility_annual, return_12m=v.return_12m,
    )
    if not (v.price and shares and v.revenue_ttm and v.revenue_ttm > 0 and ev_rev and ev_rev > 0):
        notes.append("valuation test not run: requires price, shares, positive TTM revenue and enterprise value")
        return ValuationResult(**base, revenue_required_to_double_at_current_multiple=None,
                               revenue_required_to_double_at_peer_multiple=None,
                               growth_required_to_double_at_current_multiple=None, scenarios=[],
                               bull_meets_double=None, sensitivity=[], monte_carlo=None, notes=notes)

    cash_v, debt_v = cash or 0.0, debt or 0.0
    ev_target = 2 * mcap + debt_v - cash_v
    rev_req_cur = ev_target / ev_rev
    rev_req_peer = ev_target / v.peer_ev_revenue_median if v.peer_ev_revenue_median else None
    if not v.peer_ev_revenue_median:
        notes.append("no peer EV/revenue median (fewer than 3 peers with data); peer multiple = own multiple")

    assumptions = scenario_assumptions(v, ev_rev)
    scenarios = []
    for name, a in assumptions.items():
        p = implied_price(v.revenue_ttm, a["revenue_growth"], a["ev_revenue"], debt_v, cash_v, a["fcf"], shares,
                          a["dilution"])
        scenarios.append(Scenario(
            name=name, implied_price=round(p, 4) if p is not None else None,
            upside_pct=round(p / v.price - 1, 4) if p is not None else None,
            assumptions={k: round(val, 4) for k, val in a.items()} | {
                "revenue_ttm": v.revenue_ttm, "shares": shares, "debt": debt_v, "cash": cash_v,
                "method": "EV/revenue exit multiple on 12m-forward revenue"},
        ))
    bull = next(s for s in scenarios if s.name == "bull")
    bull_meets = bull.implied_price is not None and bull.implied_price >= 2 * v.price

    grid_g = sorted({round(assumptions[k]["revenue_growth"], 4) for k in assumptions} | {0.0, round(rev_req_cur / v.revenue_ttm - 1, 4)})
    grid_m = sorted({round(assumptions[k]["ev_revenue"], 4) for k in assumptions} | {round(ev_rev, 4)})
    sens = [SensitivityCell(revenue_growth=g, ev_sales_multiple=m,
                            implied_price=implied_price(v.revenue_ttm, g, m, debt_v, cash_v, assumptions["base"]["fcf"],
                                                        shares, assumptions["base"]["dilution"]))
            for g in grid_g for m in grid_m]

    rng = np.random.default_rng(seed)
    sd_g = (assumptions["bull"]["revenue_growth"] - assumptions["bear"]["revenue_growth"]) / 3.29
    sd_m = (log(assumptions["bull"]["ev_revenue"]) - log(assumptions["bear"]["ev_revenue"])) / 3.29
    g = rng.normal(assumptions["base"]["revenue_growth"], sd_g, mc_sims)
    m = np.exp(rng.normal(log(assumptions["base"]["ev_revenue"]), sd_m, mc_sims))
    d = rng.uniform(assumptions["bull"]["dilution"], max(assumptions["bear"]["dilution"], assumptions["bull"]["dilution"] + 1e-9), mc_sims)
    f = rng.uniform(assumptions["bear"]["fcf"], assumptions["bull"]["fcf"] + 1e-9, mc_sims)
    equity = np.maximum(m * v.revenue_ttm * (1 + g) - debt_v + np.maximum(cash_v + f, 0), 0)
    prices = equity / (shares * (1 + d))
    mc = MonteCarloResult(
        simulations=mc_sims, seed=seed, p_double=float(np.mean(prices >= 2 * v.price)),
        p_loss_50=float(np.mean(prices <= 0.5 * v.price)), median_price=float(np.median(prices)),
        p5_price=float(np.percentile(prices, 5)), p95_price=float(np.percentile(prices, 95)),
        inputs={"growth_mean": assumptions["base"]["revenue_growth"], "growth_sd": sd_g,
                "ev_revenue_log_mean": log(assumptions["base"]["ev_revenue"]), "ev_revenue_log_sd": sd_m,
                "dilution_range": [assumptions["bull"]["dilution"], assumptions["bear"]["dilution"]],
                "fcf_range": [assumptions["bear"]["fcf"], assumptions["bull"]["fcf"]]},
    )
    if v.volatility_annual:
        # Driftless lognormal reference: chance the price alone touches 2x by expiry given realized volatility.
        sigma = v.volatility_annual
        from statistics import NormalDist
        p_vol = 1 - NormalDist().cdf((log(2) + 0.5 * sigma**2) / sigma)
        mc.inputs["volatility_reference_p_double_driftless"] = round(p_vol, 4)
    return ValuationResult(
        **base, revenue_required_to_double_at_current_multiple=rev_req_cur,
        revenue_required_to_double_at_peer_multiple=rev_req_peer,
        growth_required_to_double_at_current_multiple=rev_req_cur / v.revenue_ttm - 1,
        scenarios=scenarios, bull_meets_double=bull_meets, sensitivity=sens, monte_carlo=mc, notes=notes,
    )


def peer_medians(ev_rev_by_ticker: dict[str, tuple[str | None, float | None]], min_peers: int = 3) -> dict[str, float]:
    """Median EV/revenue per sector, from the analyzed cross-section (excluding non-positive multiples)."""
    groups: dict[str, list[float]] = {}
    for _, (sector, mult) in ev_rev_by_ticker.items():
        if sector and mult and mult > 0:
            groups.setdefault(sector, []).append(mult)
    return {s: float(np.median(v)) for s, v in groups.items() if len(v) >= min_peers}


def peer_median_excluding(ticker: str, sector: str | None, ev_rev_by_ticker: dict[str, tuple[str | None, float | None]],
                          min_peers: int = 3) -> float | None:
    vals = [m for t, (s, m) in ev_rev_by_ticker.items() if t != ticker and s == sector and m and m > 0]
    return float(np.median(vals)) if len(vals) >= min_peers else None


__all__ = ["ValuationInputs", "value", "implied_price", "peer_medians", "peer_median_excluding"]
