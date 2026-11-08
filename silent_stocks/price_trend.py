"""Daily price trend for the disclosed public companies.

The weekday pipeline records each new print and flags a move of at least DRASTIC_MOVE_PCT
versus the prior session. A flagged move is an alert, not a research buy.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import DRASTIC_MOVE_PCT, TRACKED_COMPANIES, Settings

ET = ZoneInfo("America/New_York")


def tracked_symbols() -> list[str]:
    return [c["symbol"] for c in TRACKED_COMPANIES]


def _blank_state() -> dict:
    return {"threshold_pct": DRASTIC_MOVE_PCT, "symbols": {
        c["symbol"]: {"name": c["name"], "role": c["role"], "observations": [], "alerted": []}
        for c in TRACKED_COMPANIES
    }}


def load_state(path: Path) -> dict:
    state = _blank_state()
    if path.exists():
        raw = json.loads(path.read_text())
        for sym, rec in (raw.get("symbols") or {}).items():
            if sym in state["symbols"]:
                state["symbols"][sym]["observations"] = list(rec.get("observations") or [])
                state["symbols"][sym]["alerted"] = list(rec.get("alerted") or [])
    state["threshold_pct"] = DRASTIC_MOVE_PCT
    return state


def _day(raw: str) -> str:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ET).strftime("%Y-%m-%d")


def _as_of_et(raw: str) -> str:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ET).strftime("%Y-%m-%d %H:%M ET")


def trend_label(observations: list[dict]) -> str:
    if len(observations) < 2:
        return "baseline"
    window = observations[-6:]
    changes = [b["price"] / a["price"] - 1 for a, b in zip(window, window[1:]) if a["price"]]
    net = window[-1]["price"] / window[0]["price"] - 1
    ups = sum(c > 0 for c in changes)
    downs = sum(c < 0 for c in changes)
    if net >= 0.02 and ups >= len(changes) / 2:
        return "rising"
    if net <= -0.02 and downs >= len(changes) / 2:
        return "falling"
    return "flat"


def apply_prints(state: dict, prints: dict[str, list[dict]], threshold: float = DRASTIC_MOVE_PCT) -> tuple[list[dict], list[dict]]:
    """prints: {symbol: [{price, price_time}]}. Returns (rows, new drastic alerts)."""
    alerts = []
    rows = []
    for spec in TRACKED_COMPANIES:
        sym = spec["symbol"]
        rec = state["symbols"][sym]
        changed = False
        for item in prints.get(sym) or []:
            price = round(float(item["price"]), 4)
            when = item["price_time"]
            day = _day(when)
            obs = rec["observations"]
            same = next((o for o in obs if o["date"] == day), None)
            if same is None:
                obs.append({"date": day, "price": price, "price_time": when})
                obs.sort(key=lambda o: o["date"])
                changed = True
            elif abs(same["price"] - price) > 0.0001:
                same["price"] = price
                same["price_time"] = when
                changed = True
        obs = rec["observations"]
        change = None
        if len(obs) >= 2:
            prev, last = obs[-2], obs[-1]
            change = last["price"] / prev["price"] - 1
            key = f"{sym}|{last['date']}|{last['price']:.4f}"
            if changed and abs(change) >= threshold and key not in rec["alerted"]:
                rec["alerted"].append(key)
                direction = "up" if change > 0 else "down"
                alerts.append({
                    "ticker": sym,
                    "kind": "price_move",
                    "message": (f"{sym} {direction} {change:+.1%} from {prev['price']:.2f} ({prev['date']}) "
                                f"to {last['price']:.2f} ({last['date']}). Tracked company; not a research buy."),
                })
        last = obs[-1] if obs else None
        rows.append({
            "symbol": sym,
            "name": spec["name"],
            "role": spec["role"],
            "price": last["price"] if last else None,
            "as_of": _as_of_et(last["price_time"]) if last else None,
            "session_date": last["date"] if last else None,
            "change_pct": change,
            "trend": trend_label(obs),
            "drastic": change is not None and abs(change) >= threshold,
            "note": f"no quote. {spec['role']}" if last is None else spec["role"],
        })
    return rows, alerts


def _state_path(settings: Settings) -> Path:
    d = settings.data_dir / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d / "price_trends.json"


def render_trend(rows: list[dict], when: datetime) -> str:
    et = when.astimezone(ET)
    lines = [
        f"# Tracked company prices — {et:%Y-%m-%d %H:%M ET}",
        "",
        "Weekday run at 09:00 America/New_York. A move of 5% or more from the prior print is flagged. "
        "A flagged move is not a research buy.",
        "",
        "| Symbol | Name | Price | As of | Vs prior print | Trend | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        price = f"{r['price']:.2f}" if r["price"] is not None else "n/a"
        change = f"{r['change_pct']:+.2%}" if r["change_pct"] is not None else "—"
        if r["drastic"]:
            change += " drastic"
        lines.append(f"| {r['symbol']} | {r['name']} | {price} | {r['as_of'] or 'n/a'} | {change} | {r['trend']} | {r['note']} |")
    lines.append("")
    return "\n".join(lines)


def write_trend_report(settings: Settings, rows: list[dict], when: datetime) -> Path:
    et = when.astimezone(ET)
    out = settings.reports_dir / "trends"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{et:%Y-%m-%d}.md"
    path.write_text(render_trend(rows, when))
    return path


def update_from_market(settings: Settings, market, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    path = _state_path(settings)
    state = load_state(path)
    prints: dict[str, list[dict]] = {}
    for spec in TRACKED_COMPANIES:
        md = market.get(spec["symbol"]) if market is not None else None
        if md is not None and md.price and md.price_time:
            prints[spec["symbol"]] = [{"price": float(md.price), "price_time": md.price_time.isoformat()}]
    rows, alerts = apply_prints(state, prints)
    path.write_text(json.dumps(state, indent=2))
    report = write_trend_report(settings, rows, now)
    return {"rows": rows, "alerts": alerts, "report": report}
