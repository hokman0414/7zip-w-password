"""Portfolio risk assessment and risk-reducing trade PROPOSALS.

This module never places orders. Each proposal carries the exact parameters a human (or an MCP session acting on a
human's explicit approval) would pass to Robinhood `review_equity_order` first, then `place_equity_order`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from math import log, sqrt

import numpy as np

from .models import CompanyReport, Status

APPROVAL = "PROPOSED — requires human approval; not submitted"


@dataclass
class RiskLimits:
    max_position_weight: float = 0.10
    trim_to_weight: float = 0.08
    max_fund_weight: float = 0.20
    fund_trim_to_weight: float = 0.18
    max_leveraged_etf_weight: float = 0.03
    high_vol_threshold: float = 0.80
    max_high_vol_weight: float = 0.04
    vetoed_max_weight: float = 0.01
    target_beta: float = 1.0
    beta_tolerance: float = 0.15
    cash_reserve: float = 0.05
    max_new_position_weight: float = 0.04
    min_trade_usd: float = 5.0
    dust_usd: float = 1.0


@dataclass
class Holding:
    symbol: str
    quantity: float
    price: float
    monthly_closes: list[float]
    asset_type: str | None = None
    leverage: float | None = None
    value: float = 0.0
    weight: float = 0.0
    vol: float | None = None
    beta: float | None = None
    report_status: str | None = None
    critical_vetoes: list[str] = field(default_factory=list)


def _rets(closes: list[float], price: float) -> list[float]:
    s = [c for c in closes if c and c > 0] + [price]
    return [log(b / a) for a, b in zip(s, s[1:])]


def _beta(r: list[float], m: list[float]) -> float | None:
    n = min(len(r), len(m))
    if n < 6:
        return None
    a, b = np.array(r[-n:]), np.array(m[-n:])
    var = float(np.var(b, ddof=1))
    if var <= 0:
        return None
    raw = float(np.cov(a, b, ddof=1)[0, 1] / var)
    # Blume shrinkage toward 1: 12 monthly observations give very noisy raw betas.
    return 0.67 * raw + 0.33


FUND_TYPES = {"commodity_etf", "country_etf", "index_etf"}


def _limit(h: "Holding", lim: "RiskLimits") -> tuple[float, float]:
    if h.asset_type in FUND_TYPES:
        return lim.max_fund_weight, lim.fund_trim_to_weight
    return lim.max_position_weight, lim.trim_to_weight


def assess(snapshot: dict, reports: dict[str, CompanyReport] | None = None, limits: RiskLimits | None = None) -> dict:
    lim = limits or RiskLimits()
    pos = snapshot["positions"]
    port = pos["portfolio"]
    bench = pos["benchmark"]
    m_rets = _rets(bench["monthly_closes"], bench["price"])
    total = float(port["total_value"])
    holdings: list[Holding] = []
    for h in pos["holdings"]:
        x = Holding(h["symbol"], float(h["quantity"]), float(h["price"]), list(h.get("monthly_closes") or []),
                    h.get("asset_type"), h.get("leverage"))
        x.value = x.quantity * x.price
        x.weight = x.value / total if total else 0.0
        r = _rets(x.monthly_closes, x.price)
        x.vol = float(np.std(r, ddof=1) * sqrt(12)) if len(r) >= 6 else None
        x.beta = _beta(r, m_rets)
        rep = (reports or {}).get(x.symbol)
        if rep:
            x.report_status = rep.status.value
            x.critical_vetoes = [v.code for v in rep.vetoes if v.severity == "critical"]
        holdings.append(x)
    live = [h for h in holdings if h.value >= lim.dust_usd]
    equity_w = sum(h.weight for h in live)
    known_beta = [h for h in live if h.beta is not None]
    beta_cov = sum(h.weight for h in known_beta)
    port_beta = sum(h.weight * h.beta for h in known_beta) / beta_cov * equity_w if beta_cov else None

    full = [h for h in live if len(_rets(h.monthly_closes, h.price)) >= 11]
    port_vol = None
    clusters: list[list[str]] = []
    if len(full) >= 2:
        n = min(len(_rets(h.monthly_closes, h.price)) for h in full)
        R = np.array([_rets(h.monthly_closes, h.price)[-n:] for h in full])
        w = np.array([h.weight for h in full])
        cov = np.cov(R, ddof=1) * 12
        port_vol = float(sqrt(max(w @ cov @ w, 0.0)) / w.sum() * equity_w)
        corr = np.corrcoef(R)
        seen: set[int] = set()
        for i in range(len(full)):
            if i in seen:
                continue
            grp = [j for j in range(len(full)) if j != i and corr[i, j] > 0.75 and j not in seen]
            if grp:
                seen |= {i, *grp}
                clusters.append(sorted([full[i].symbol] + [full[j].symbol for j in grp]))
    hhi = sum(h.weight ** 2 for h in live)
    flags = []
    for h in live:
        cap, _ = _limit(h, lim)
        if h.weight > cap:
            flags.append({"symbol": h.symbol, "flag": "concentration", "detail": f"{h.weight:.1%} > {cap:.0%} {'fund' if h.asset_type in FUND_TYPES else 'single-name'} limit"})
        if h.leverage and h.leverage > 1:
            flags.append({"symbol": h.symbol, "flag": "leveraged_etf", "detail": f"{h.leverage:.0f}x daily-reset product: volatility decay over multi-month holds"})
        if h.vol and h.vol > lim.high_vol_threshold:
            flags.append({"symbol": h.symbol, "flag": "high_volatility", "detail": f"realized vol {h.vol:.0%} (monthly, annualized)"})
        if h.critical_vetoes:
            flags.append({"symbol": h.symbol, "flag": "research_veto", "detail": ", ".join(h.critical_vetoes)})
    for c in clusters:
        w = sum(h.weight for h in live if h.symbol in c)
        if w > 0.20:
            flags.append({"symbol": "+".join(c), "flag": "correlated_cluster", "detail": f"{w:.1%} in names with pairwise return correlation > 0.75"})
    if port_beta is not None and port_beta > lim.target_beta + lim.beta_tolerance:
        flags.append({"symbol": "PORTFOLIO", "flag": "high_beta", "detail": f"beta {port_beta:.2f} vs target {lim.target_beta:.2f}"})
    if float(port.get("cash") or 0) / total < lim.cash_reserve if total else False:
        flags.append({"symbol": "PORTFOLIO", "flag": "no_cash_reserve", "detail": f"cash {float(port.get('cash') or 0):.2f} < {lim.cash_reserve:.0%} reserve"})
    return {"total_value": total, "cash": float(port.get("cash") or 0), "crypto_value": float(port.get("crypto_value") or 0),
            "holdings": holdings, "portfolio_beta": port_beta, "portfolio_vol": port_vol, "hhi": hhi,
            "effective_positions": 1 / hhi if hhi else None, "clusters": clusters, "flags": flags,
            "account_type": pos.get("account_type"), "option_level": pos.get("option_level"),
            "method": ("monthly log returns, last 12 months vs SPY; betas Blume-adjusted (0.67*raw+0.33); "
                       "directly held crypto has no beta estimate and is excluded from beta; historical estimates, not forecasts")}


def _order(symbol: str, side: str, *, quantity: float | None = None, dollar_amount: float | None = None) -> dict:
    p = {"account_number": os.environ.get("ROBINHOOD_AGENTIC_ACCOUNT", "<set ROBINHOOD_AGENTIC_ACCOUNT>"),
         "symbol": symbol, "side": side, "type": "market", "time_in_force": "gfd", "market_hours": "regular_hours"}
    if quantity is not None:
        p["quantity"] = f"{quantity:.6f}"
    else:
        p["dollar_amount"] = f"{dollar_amount:.2f}"
    return p


def propose(risk: dict, reports: dict[str, CompanyReport] | None = None, limits: RiskLimits | None = None,
            hedge_symbol: str = "SH") -> list[dict]:
    lim = limits or RiskLimits()
    total = risk["total_value"]
    out: list[dict] = []
    proceeds = 0.0
    target_w: dict[str, float] = {}
    for h in risk["holdings"]:
        if h.value < lim.dust_usd:
            continue
        cap, trim_to = _limit(h, lim)
        caps = [(trim_to, f"weight {h.weight:.1%} above {cap:.0%} {'fund' if h.asset_type in FUND_TYPES else 'single-name'} limit")] if h.weight > cap else []
        if h.leverage and h.leverage > 1 and h.weight > lim.max_leveraged_etf_weight:
            caps.append((lim.max_leveraged_etf_weight, f"{h.leverage:.0f}x leveraged ETF at {h.weight:.1%}; cap {lim.max_leveraged_etf_weight:.0%}"))
        if h.vol and h.vol > lim.high_vol_threshold and h.weight > lim.max_high_vol_weight:
            caps.append((lim.max_high_vol_weight, f"realized vol {h.vol:.0%} at {h.weight:.1%}; high-vol cap {lim.max_high_vol_weight:.0%}"))
        if h.critical_vetoes and h.weight > lim.vetoed_max_weight:
            caps.append((lim.vetoed_max_weight, f"research critical veto ({', '.join(h.critical_vetoes)}); cap {lim.vetoed_max_weight:.0%}"))
        if not caps:
            continue
        tw, _ = min(caps)
        sell_usd = (h.weight - tw) * total
        if sell_usd < lim.min_trade_usd:
            continue
        qty = min(round(sell_usd / h.price, 6), h.quantity)
        target_w[h.symbol] = tw
        proceeds += qty * h.price
        out.append({"symbol": h.symbol, "side": "sell", "quantity": qty, "est_value": round(qty * h.price, 2),
                    "order_type": "market", "from_weight": round(h.weight, 4), "to_weight": tw,
                    "rationale": "; ".join(r for _, r in caps), "kind": "risk_trim", "status": APPROVAL,
                    "review_equity_order": _order(h.symbol, "sell", quantity=qty)})

    beta_after = None
    if risk["portfolio_beta"] is not None:
        beta_after = risk["portfolio_beta"]
        for h in risk["holdings"]:
            if h.symbol in target_w and h.beta is not None:
                beta_after -= (h.weight - target_w[h.symbol]) * h.beta
    reserve = lim.cash_reserve * total - risk["cash"]
    available = proceeds - max(reserve, 0.0)
    if beta_after is not None and beta_after > lim.target_beta + lim.beta_tolerance:
        need = (beta_after - lim.target_beta) * total
        hedge = min(need, max(available, 0.0))
        if risk.get("option_level"):
            note = "options enabled: protective SPY puts are an alternative; not sized here"
        else:
            note = "account has no options level, so the hedge uses a -1x inverse S&P 500 ETF (daily reset; review weekly)"
        if hedge >= lim.min_trade_usd:
            out.append({"symbol": hedge_symbol, "side": "buy", "dollar_amount": round(hedge, 2), "order_type": "market",
                        "rationale": f"portfolio beta {beta_after:.2f} after trims vs target {lim.target_beta:.2f}; "
                                     f"${need:,.0f} short-beta needed, sized to available proceeds; {note}",
                        "kind": "hedge", "status": APPROVAL,
                        "review_equity_order": _order(hedge_symbol, "buy", dollar_amount=hedge)})
            available -= hedge
        else:
            out.append({"symbol": hedge_symbol, "side": "none", "rationale": f"beta {beta_after:.2f} above target but no free proceeds after cash reserve; trim high-beta names further or add cash",
                        "kind": "hedge_unfunded", "status": "INFORMATIONAL"})

    qualified = [r for r in (reports or {}).values() if r.status == Status.QUALIFIED and r.price]
    held = {h.symbol for h in risk["holdings"] if h.value >= lim.dust_usd}
    if not qualified:
        out.append({"symbol": "-", "side": "none", "kind": "no_buy",
                    "rationale": "No candidate passed the 80/100 independent-evidence gate with bull case >= 2x and no critical veto; "
                                 "no buy proposals. Proceeds stay as cash reserve.", "status": "INFORMATIONAL"})
    else:
        per = min(lim.max_new_position_weight * total, max(available, 0.0) / max(len(qualified), 1))
        for r in sorted(qualified, key=lambda r: r.tally.independent_yes, reverse=True):
            if r.ticker in held or per < lim.min_trade_usd:
                continue
            out.append({"symbol": r.ticker, "side": "buy", "dollar_amount": round(per, 2), "order_type": "market",
                        "rationale": f"QUALIFIED ({r.tally.independent_yes}/100 independent YES); starter position capped at {lim.max_new_position_weight:.0%}",
                        "kind": "research_buy", "status": APPROVAL,
                        "review_equity_order": _order(r.ticker, "buy", dollar_amount=per)})
    return out
