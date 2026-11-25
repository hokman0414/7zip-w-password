"""Growth-profile ETF allocation.

Loads `config/allocation.json` and turns weight gaps into proposals. This module never
places orders. Growth buys are separate from `core_reinvest` and are not blocked by the
SPY 10-month trend pause; that pause only stops mindless idle-cash reinvestment.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import ROOT
from .portfolio_risk import APPROVAL, FUND_TYPES, _order

DEFAULT_PATH = ROOT / "config" / "allocation.json"


def load_allocation(path: Path | None = None) -> dict | None:
    path = path or DEFAULT_PATH
    if not path.exists():
        return None
    return json.loads(path.read_text())


def sleeve_members(allocation: dict) -> dict[str, str]:
    """Map every symbol (primary or alias) to its sleeve primary symbol."""
    out: dict[str, str] = {}
    for sleeve in allocation.get("sleeves") or []:
        primary = sleeve["symbol"]
        out[primary] = primary
        for alias in sleeve.get("aliases") or []:
            out[alias] = primary
    return out


def current_sleeve_weights(risk: dict, allocation: dict) -> dict[str, float]:
    members = sleeve_members(allocation)
    weights = {s["symbol"]: 0.0 for s in allocation.get("sleeves") or []}
    for h in risk["holdings"]:
        primary = members.get(h.symbol)
        if primary:
            weights[primary] = weights.get(primary, 0.0) + h.weight
    return weights


def growth_etf_weight(risk: dict, allocation: dict) -> float:
    members = sleeve_members(allocation)
    return sum(h.weight for h in risk["holdings"] if h.symbol in members)


def propose_allocation(risk: dict, allocation: dict | None = None, limits=None) -> list[dict]:
    """Sell non-sleeve funds toward zero; buy underweight growth sleeves from spendable cash."""
    from .portfolio_risk import RiskLimits

    lim = limits or RiskLimits()
    alloc = allocation or load_allocation()
    if not alloc or alloc.get("profile") != "growth":
        return []
    members = sleeve_members(alloc)
    banned = set(alloc.get("do_not_buy") or [])
    total = risk["total_value"]
    out: list[dict] = []
    proceeds = 0.0

    # 1) Sell funds that are not part of a growth sleeve (largest first so the daily order cap hits them).
    non_sleeve = sorted(
        (h for h in risk["holdings"]
         if h.symbol not in members and h.asset_type in FUND_TYPES and h.value >= lim.dust_usd and h.weight > 0),
        key=lambda h: h.value, reverse=True,
    )
    for h in non_sleeve:
        sell_usd = h.weight * total
        if sell_usd < lim.min_trade_usd:
            continue
        qty = min(round(sell_usd / h.price, 6), h.available if h.available is not None else h.quantity)
        if qty * h.price < lim.min_trade_usd:
            continue
        proceeds += qty * h.price
        out.append({
            "symbol": h.symbol, "side": "sell", "quantity": qty, "est_value": round(qty * h.price, 2),
            "order_type": "market", "from_weight": round(h.weight, 4), "to_weight": 0.0,
            "rationale": (f"growth profile: {h.symbol} is not a selected growth sleeve "
                          f"(target sleeves {[s['symbol'] for s in alloc['sleeves']]}); sell toward 0"),
            "kind": "growth_rebalance", "status": APPROVAL,
            "review_equity_order": _order(h.symbol, "sell", quantity=qty),
        })

    # 2) Buy underweight sleeves from cash already spendable above the reserve.
    available = max(risk.get("cash_spendable", risk["cash"]) - lim.cash_reserve * total, 0.0)
    weights = current_sleeve_weights(risk, alloc)
    held = {h.symbol: h for h in risk["holdings"]}
    for sleeve in sorted(alloc.get("sleeves") or [], key=lambda s: s["target_weight"], reverse=True):
        sym = sleeve["symbol"]
        if sym in banned:
            continue
        gap = sleeve["target_weight"] - weights.get(sym, 0.0)
        if gap <= 0:
            continue
        need = gap * total
        # Prefer the cheaper primary when an alias is already held (e.g. migrate QQQ -> QQQM later);
        # for new cash, buy the primary.
        buy_sym = sym
        price = None
        if buy_sym in held:
            price = held[buy_sym].price
        elif any(a in held for a in sleeve.get("aliases") or []):
            # Sleeve weight already includes aliases; still buy the primary to complete the sleeve.
            pass
        amt = min(need, available)
        if amt < lim.min_trade_usd:
            if need >= lim.min_trade_usd:
                out.append({
                    "symbol": buy_sym, "side": "none", "kind": "growth_rebalance_unfunded",
                    "status": "INFORMATIONAL",
                    "rationale": (f"growth sleeve {buy_sym} is {weights.get(sym, 0):.1%} vs target "
                                  f"{sleeve['target_weight']:.0%}; ${need:,.0f} needed, "
                                  f"waiting on sale proceeds / cash above the reserve"),
                })
            continue
        # Cap one buy at the fund weight limit so a single fill cannot breach concentration.
        room = lim.max_fund_weight * total - (held[buy_sym].value if buy_sym in held else 0.0)
        amt = min(amt, max(room, 0.0))
        if amt < lim.min_trade_usd:
            continue
        available -= amt
        out.append({
            "symbol": buy_sym, "side": "buy", "dollar_amount": round(amt, 2), "order_type": "market",
            "rationale": (f"growth sleeve {buy_sym} at {weights.get(sym, 0):.1%} vs target "
                          f"{sleeve['target_weight']:.0%} ({sleeve['role']}); {sleeve['rationale']}"),
            "kind": "growth_rebalance", "status": APPROVAL,
            "review_equity_order": _order(buy_sym, "buy", dollar_amount=amt),
            "ref_price": price,
        })

    growth_w = growth_etf_weight(risk, alloc)
    out.insert(0, {
        "symbol": "PORTFOLIO", "side": "none", "kind": "growth_allocation_status",
        "status": "INFORMATIONAL",
        "rationale": (f"growth profile: selected ETFs are {growth_w:.1%} of the account vs "
                      f"{alloc['etf_target_weight']:.0%} target "
                      f"(sleeves {', '.join(f'{s['symbol']} {s['target_weight']:.0%}' for s in alloc['sleeves'])})"),
        "growth_etf_weight": round(growth_w, 4),
        "target_weight": alloc["etf_target_weight"],
        "sleeve_weights": {k: round(v, 4) for k, v in weights.items()},
    })
    return out
