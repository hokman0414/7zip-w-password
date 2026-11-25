"""Parse a trading request into sized orders.

The steps follow the day-trader skill (scanner, exit, budget, risk, broker) and
pstack potato mode: one playbook, copied as steps, then the next request reads
what the last fills did. This module never sends an order. A sell that only
reduces shares already held is an exit. An entry still has to pass the daily
plan.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from .config import Settings
from .execution import ET, HOLIDAYS, AutotradeConfig

STOPWORDS = {
    "AI", "ALL", "AN", "AND", "AS", "AT", "BE", "BY", "DO", "ET", "FOR", "FROM", "HEAVY",
    "HIGH", "I", "IF", "IN", "IS", "IT", "MY", "OF", "ON", "OR", "PM", "RISK", "THE",
    "TO", "US", "USE", "WE",
}
TICKER = re.compile(r"\b([A-Z]{1,5}(?:\.[A-Z])?)\b")
VERBS = ("exit", "trim", "review", "buy")

DEFAULT_RULES = {
    "fractions": {"exit": 1.0, "trim_thesis_fails": 0.5, "trim_thesis_holds": 0.25, "review": 0.0},
    "step": 0.25,
    "move_threshold": 0.05,
    "min_sessions": 3,
    "learned": [],
    "gaps": [{
        "as_of": "2026-11-21",
        "source": "2026-11-20 fills",
        "gap": (
            "The BITU exit sold the whole position, which matches fraction 1.0. "
            "NBIS, CIFR and IREN were red-team failures and were cut in half, so a failed thesis now trims 0.5. "
            "DRAM had no company report and was also cut in half, so a named trim with no ACH or red-team result is unconfirmed and uses 0.5. "
            "A thesis that still stands trims 0.25. WDC, SNDK and WULF were not held. "
            "A later price move of 5% raises or cuts the failed-thesis fraction by 0.25."
        ),
    }],
}


def sat_index(reports) -> dict[str, dict]:
    out = {}
    for report in reports:
        techniques = getattr(report, "techniques", []) or []
        ach = next((t for t in techniques if t.technique == "Analysis of Competing Hypotheses"), None)
        red = next((t for t in techniques if t.technique == "Red Team Analysis"), None)
        out[report.ticker] = {
            "leading": (ach.details.get("leading") if ach else None),
            "red_team_survives": (red.details.get("survives") if red else None),
        }
    return out


def load_rules(settings: Settings) -> dict:
    path = settings.data_dir / "state" / "playbook_rules.json"
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_RULES))
    return json.loads(path.read_text())


def save_rules(settings: Settings, rules: dict) -> None:
    path = settings.data_dir / "state" / "playbook_rules.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rules, indent=2))


def _verb(segment: str) -> str | None:
    low = segment.lower()
    for verb in VERBS:
        if re.search(rf"\b{verb}\b", low):
            return verb
    return None


def parse_request(text: str) -> list[dict]:
    """Symbols inherit the verb in their own line. Exit wins over trim, trim over review."""
    intents = []
    seen = set()
    for segment in re.split(r"[\n;]+", text):
        verb = _verb(segment)
        if not verb:
            continue
        theme = " ".join(segment.split())
        for symbol in TICKER.findall(segment):
            if symbol in STOPWORDS or (symbol, verb) in seen:
                continue
            seen.add((symbol, verb))
            intents.append({"symbol": symbol, "verb": verb, "theme": theme})
    return intents


def _fraction(verb: str, sat: dict, rules: dict) -> tuple[float, str]:
    fractions = rules["fractions"]
    if verb == "exit":
        return fractions["exit"], "exit"
    if verb == "review":
        return fractions["review"], "review"
    if verb != "trim":
        return 0.0, verb
    has_report = sat.get("leading") is not None or sat.get("red_team_survives") is not None
    fails = (
        not has_report
        or sat.get("red_team_survives") is False
        or sat.get("leading") in ("H3", "H4")
        or sat.get("leveraged")
    )
    key = "trim_thesis_fails" if fails else "trim_thesis_holds"
    return fractions[key], key


def _rationale(verb: str, rule: str, fraction: float, sat: dict, theme: str) -> str:
    note = ""
    if rule == "trim_thesis_fails" and sat.get("leading") is None and sat.get("red_team_survives") is None and not sat.get("leveraged"):
        note = " No structured report, so the thesis is unconfirmed."
    return f"{verb} via {rule} at fraction {fraction:.2f}.{note} {theme}".strip()


def _qty(available: float, fraction: float, price: float, max_usd: float) -> float:
    qty = min(available * fraction, max_usd / price if price else 0.0)
    return float(f"{max(qty, 0.0):.6f}")


def size_request(intents: list[dict], holdings: list[dict], sat: dict[str, dict], rules: dict,
                 limits: AutotradeConfig | None = None) -> dict:
    """Turn parsed intents into orders. Missing names and dust sizes are notes, not orders."""
    cfg = limits or AutotradeConfig(max_order_usd=400, min_order_usd=5, max_orders_per_day=6)
    held = {h["symbol"]: h for h in holdings}
    orders, notes = [], []
    for intent in intents:
        symbol, verb = intent["symbol"], intent["verb"]
        holding = held.get(symbol)
        if not holding or float(holding.get("available") or 0) <= 0:
            notes.append(f"{symbol} {verb}: not held")
            continue
        price = float(holding["price"])
        info = dict(sat.get(symbol) or {})
        if holding.get("asset_type") == "leveraged_etf":
            info["leveraged"] = True
        fraction, rule = _fraction(verb, info, rules)
        if fraction <= 0:
            notes.append(f"{symbol} {verb}: review only, no order")
            continue
        qty = _qty(float(holding["available"]), fraction, price, cfg.max_order_usd)
        usd = qty * price
        if usd < cfg.min_order_usd:
            notes.append(f"{symbol} {verb}: ${usd:.2f} is under the ${cfg.min_order_usd:.0f} minimum")
            continue
        if len(orders) >= cfg.max_orders_per_day:
            notes.append(f"{symbol} {verb}: daily order cap reached")
            continue
        orders.append({
            "symbol": symbol, "side": "sell" if verb in ("exit", "trim") else verb,
            "kind": "risk_trim", "verb": verb, "rule": rule, "fraction": fraction,
            "quantity": f"{qty:.6f}", "est_usd": round(usd, 2), "ref_price": price,
            "rationale": _rationale(verb, rule, fraction, info, intent.get("theme", "")),
        })
    return {"orders": orders, "notes": notes}


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def sessions_between(start: datetime, end: datetime) -> int:
    """NYSE sessions after the start day, through the end day."""
    day, last = start.astimezone(ET).date(), end.astimezone(ET).date()
    count = 0
    while day < last:
        day = day.fromordinal(day.toordinal() + 1)
        if day.weekday() < 5 and day.isoformat() not in HOLIDAYS:
            count += 1
    return count


def learn_from_fills(rules: dict, fills: list[dict], prices_now: dict[str, float], now: datetime) -> dict:
    """Move one trim fraction from the median move of that setup. One name cannot swing the shared rule. Exit stays 1.

    A batch (rule and fill day) is scored once, and only after `min_sessions` sessions, so a one-session bounce
    cannot move the rule and a persistent move cannot step it again every day.
    """
    updated = json.loads(json.dumps(rules))
    step = float(updated.get("step", 0.25))
    threshold = float(updated.get("move_threshold", 0.05))
    min_sessions = int(updated.get("min_sessions", 3))
    learned = set(updated.setdefault("learned", []))
    grouped: dict[str, list[tuple[str, float]]] = {}
    batches: dict[str, set[str]] = {}
    for fill in fills:
        if fill.get("side") != "sell" or fill.get("verb") == "exit":
            continue
        rule = fill.get("rule")
        if rule not in updated["fractions"] or rule == "exit" or not fill.get("filled_at"):
            continue
        filled_at = datetime.fromisoformat(fill["filled_at"].replace("Z", "+00:00"))
        key = f"{rule}:{filled_at.astimezone(ET).date().isoformat()}"
        if key in learned or sessions_between(filled_at, now) < min_sessions:
            continue
        price = prices_now.get(fill["symbol"])
        entry = float(fill.get("fill_price") or 0)
        if not price or entry <= 0:
            continue
        grouped.setdefault(rule, []).append((fill["symbol"], (price - entry) / entry))
        batches.setdefault(rule, set()).add(key)
    for rule, rows in grouped.items():
        updated["learned"] = sorted(set(updated["learned"]) | batches[rule])
        median = _median([move for _, move in rows])
        before = updated["fractions"][rule]
        detail = ", ".join(f"{symbol} {move:+.1%}" for symbol, move in rows)
        if median <= -threshold:
            updated["fractions"][rule] = min(1.0, round(before + step, 2))
            direction = "fell"
        elif median >= threshold:
            updated["fractions"][rule] = max(step, round(before - step, 2))
            direction = "rose"
        else:
            updated.setdefault("gaps", []).append({
                "as_of": now.date().isoformat(),
                "source": rule,
                "gap": (
                    f"{rule} median move {median:+.1%} ({detail}). "
                    f"That is inside 5%, so the fraction stays {before:.2f}."
                ),
            })
            continue
        after = updated["fractions"][rule]
        updated.setdefault("gaps", []).append({
            "as_of": now.date().isoformat(),
            "source": rule,
            "gap": (
                f"{rule} median {direction} {median:+.1%} ({detail}). "
                f"Fraction {before:.2f} -> {after:.2f}."
            ),
        })
    return updated
