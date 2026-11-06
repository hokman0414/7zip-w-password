"""Guardrailed order planning and execution records.

Python cannot reach the Robinhood MCP, so execution is split:
  1. `plan_orders` turns the day's risk proposals into an order plan that passed every guardrail.
  2. The agent session (see .cursor/skills/silent-stocks-daily) calls review_equity_order, then place_equity_order,
     for exactly the orders in the plan, re-checking the live quote against `max_quote_drift_pct`.
  3. `record_executions` stores the broker responses and updates persistent state (cooldowns, high-water mark).

Live trading is armed only when ALL hold: config enabled, ROBINHOOD_AGENTIC_ACCOUNT set and matching account_last4,
no kill switch (data/STOP_TRADING or SILENT_STOP=1), a weekday inside the execution window, a fresh snapshot that
passed validation. The full account number is never written to disk.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import ROOT, Settings

ET = ZoneInfo("America/New_York")
ACCOUNT_PLACEHOLDER = "$ROBINHOOD_AGENTIC_ACCOUNT"
# NYSE full-day closures; orders on these days would queue to the next open at an unknown price.
HOLIDAYS = {"2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
            "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"}


@dataclass
class AutotradeConfig:
    enabled: bool = False
    account_last4: str = ""
    allowed_kinds: list[str] = field(default_factory=lambda: ["risk_trim"])
    reinvest_symbol: str | None = None
    hedge_symbol: str = "SH"
    max_order_usd: float = 400.0
    max_daily_turnover_pct: float = 0.20
    max_orders_per_day: int = 6
    min_order_usd: float = 5.0
    cash_reserve_pct: float = 0.05
    drawdown_halt_buys_pct: float = 0.15
    drawdown_halt_all_pct: float = 0.30
    symbol_cooldown_days: int = 3
    max_snapshot_age_hours: float = 6.0
    max_quote_drift_pct: float = 0.05
    execution_window_et: list[str] = field(default_factory=lambda: ["09:45", "15:30"])

    @classmethod
    def load(cls, path: Path | None = None) -> "AutotradeConfig":
        path = path or ROOT / "config" / "autotrade.json"
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text())
        return cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})


def state_dir(settings: Settings) -> Path:
    d = settings.data_dir / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_state(settings: Settings) -> dict:
    p = state_dir(settings) / "autotrade_state.json"
    return json.loads(p.read_text()) if p.exists() else {"high_water_mark": None, "last_trades": {}, "executions": 0}


def save_state(settings: Settings, state: dict) -> None:
    (state_dir(settings) / "autotrade_state.json").write_text(json.dumps(state, indent=2, sort_keys=True))


def arming_status(cfg: AutotradeConfig, settings: Settings, now: datetime) -> list[str]:
    """Empty list means armed; otherwise the reasons live orders are blocked."""
    why = []
    if not cfg.enabled:
        why.append("autotrade disabled in config/autotrade.json")
    acct = os.environ.get("ROBINHOOD_AGENTIC_ACCOUNT", "")
    if not acct:
        why.append("ROBINHOOD_AGENTIC_ACCOUNT secret not set")
    elif not acct.endswith(cfg.account_last4):
        why.append("ROBINHOOD_AGENTIC_ACCOUNT does not match account_last4")
    if os.environ.get("SILENT_STOP") == "1" or (settings.data_dir / "STOP_TRADING").exists():
        why.append("kill switch active (data/STOP_TRADING or SILENT_STOP=1)")
    et = now.astimezone(ET)
    if et.weekday() >= 5 or et.strftime("%Y-%m-%d") in HOLIDAYS:
        why.append(f"market closed on {et:%a %Y-%m-%d}")
    lo, hi = cfg.execution_window_et
    if not (lo <= et.strftime("%H:%M") <= hi):
        why.append(f"outside execution window {lo}-{hi} ET (now {et:%H:%M})")
    return why


def _ref_id(day: str, symbol: str, side: str, kind: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"silent-stocks/{day}/{symbol}/{side}/{kind}"))


def plan_orders(cfg: AutotradeConfig, settings: Settings, proposals: list[dict], portfolio_doc: dict,
                validation_errors: list[str], now: datetime, state: dict) -> dict:
    day = now.astimezone(ET).strftime("%Y-%m-%d")
    pos = portfolio_doc["positions"]
    total = float(pos["portfolio"]["total_value"])
    captured = datetime.fromisoformat(portfolio_doc["captured_at"].replace("Z", "+00:00"))
    blocked = arming_status(cfg, settings, now)
    age_h = (now - captured).total_seconds() / 3600
    if age_h > cfg.max_snapshot_age_hours:
        blocked.append(f"portfolio snapshot {age_h:.1f}h old > {cfg.max_snapshot_age_hours}h")
    if validation_errors:
        blocked.append(f"snapshot validation failed: {'; '.join(validation_errors[:3])}")

    hwm = max(filter(None, [state.get("high_water_mark"), total]))
    drawdown = 1 - total / hwm if hwm else 0.0
    buys_halted = drawdown >= cfg.drawdown_halt_buys_pct
    if drawdown >= cfg.drawdown_halt_all_pct:
        blocked.append(f"drawdown {drawdown:.0%} from high-water mark >= {cfg.drawdown_halt_all_pct:.0%}: all trading halted")

    held = {h["symbol"]: h for h in pos["holdings"]}
    spendable = min(float(pos["portfolio"].get("cash") or 0), float(pos["portfolio"].get("buying_power", pos["portfolio"].get("cash") or 0)))
    buy_budget = max(spendable - cfg.cash_reserve_pct * total, 0.0)
    turnover_left = cfg.max_daily_turnover_pct * total
    orders, rejected = [], []
    actionable = [p for p in proposals if p.get("side") in ("buy", "sell")]
    for p in sorted(actionable, key=lambda p: p["side"] != "sell"):
        sym, side, kind = p["symbol"], p["side"], p.get("kind", "")

        def reject(reason):
            rejected.append({"symbol": sym, "side": side, "kind": kind, "reason": reason})

        if kind not in cfg.allowed_kinds:
            reject(f"kind '{kind}' not in allowed_kinds")
            continue
        last = state.get("last_trades", {}).get(sym)
        if last and (now - datetime.fromisoformat(last["at"])).days < cfg.symbol_cooldown_days:
            reject(f"cooldown: traded {last['side']} on {last['at'][:10]}")
            continue
        if len(orders) >= cfg.max_orders_per_day:
            reject("max_orders_per_day reached")
            continue
        if side == "sell":
            h = held.get(sym)
            if not h:
                reject("not held")
                continue
            price = float(h["price"])
            avail = float(h.get("available", h["quantity"]))
            qty = min(float(p["quantity"]), avail, cfg.max_order_usd / price, turnover_left / price)
            qty = float(f"{qty:.6f}")
            usd = qty * price
            if usd < cfg.min_order_usd:
                reject(f"clipped below min_order_usd (turnover left ${turnover_left:,.2f})")
                continue
            params = {"symbol": sym, "side": "sell", "type": "market", "quantity": f"{qty:.6f}"}
            ref_price = price
        else:
            if buys_halted:
                reject(f"buys halted: drawdown {drawdown:.0%} >= {cfg.drawdown_halt_buys_pct:.0%}")
                continue
            usd = min(float(p["dollar_amount"]), cfg.max_order_usd, buy_budget, turnover_left)
            if usd < cfg.min_order_usd:
                reject(f"insufficient spendable cash above reserve (${buy_budget:,.2f}); proceeds fund the next run")
                continue
            usd = float(f"{usd:.2f}")
            buy_budget -= usd
            params = {"symbol": sym, "side": "buy", "type": "market", "dollar_amount": f"{usd:.2f}"}
            ref_price = float(held[sym]["price"]) if sym in held else None
        turnover_left -= usd
        params |= {"account_number": ACCOUNT_PLACEHOLDER, "time_in_force": "gfd", "market_hours": "regular_hours"}
        orders.append({"symbol": sym, "side": side, "kind": kind, "est_usd": round(usd, 2), "ref_price": ref_price,
                       "max_quote_drift_pct": cfg.max_quote_drift_pct, "rationale": p["rationale"],
                       "ref_id": _ref_id(day, sym, side, kind), "params": params,
                       "clipped": bool(side == "sell" and float(params["quantity"]) < float(p["quantity"]) - 1e-6)})
    return {"date": day, "created_at": now.isoformat(), "armed": not blocked, "blocked_reasons": blocked,
            "drawdown_from_hwm": round(drawdown, 4), "high_water_mark": hwm, "buys_halted": buys_halted,
            "orders": orders if not blocked else [], "would_place_if_armed": orders if blocked else [],
            "rejected": rejected,
            "instructions": ("Sells first. For each order: substitute ROBINHOOD_AGENTIC_ACCOUNT, call review_equity_order; "
                             "skip if order_checks/alerts are non-empty or the quoted price drifts more than "
                             "max_quote_drift_pct from ref_price; otherwise call place_equity_order with the same params and ref_id. "
                             "Never place an order that is not in `orders`.")}


def write_plan(settings: Settings, plan: dict) -> Path:
    d = settings.data_dir / "orders"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{plan['date']}.json"
    p.write_text(json.dumps(plan, indent=2, default=str))
    return p


def record_executions(settings: Settings, results: list[dict], now: datetime, total_value: float | None = None) -> Path:
    """results: [{ref_id, symbol, side, status: placed|skipped|failed, reason?, order_id?, broker_state?, usd?}]"""
    day = now.astimezone(ET).strftime("%Y-%m-%d")
    d = settings.data_dir / "executions"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{day}.json"
    prior = json.loads(p.read_text()) if p.exists() else []
    seen = {r["ref_id"] for r in prior if r.get("ref_id")}
    for r in results:
        if r.get("account_number"):
            raise ValueError("execution records must not contain the account number")
        if r.get("ref_id") in seen:
            continue
        prior.append(r | {"recorded_at": now.isoformat()})
    p.write_text(json.dumps(prior, indent=2, default=str))
    st = load_state(settings)
    for r in results:
        if r.get("status") == "placed":
            st.setdefault("last_trades", {})[r["symbol"]] = {"side": r["side"], "at": now.isoformat(), "ref_id": r.get("ref_id")}
            st["executions"] = st.get("executions", 0) + 1
    if total_value:
        st["high_water_mark"] = max(filter(None, [st.get("high_water_mark"), total_value]))
    save_state(settings, st)
    return p


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


__all__ = ["AutotradeConfig", "plan_orders", "write_plan", "record_executions", "arming_status", "load_state"]
