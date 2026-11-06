"""Daily refresh helpers for the agent session: which symbols to fetch from the Robinhood MCP, snapshot validation
(catches transcription errors before anything trades), and which tickers need fresh deep research."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .config import DEFAULT_WATCHLIST, Settings
from .connectors.research import AgentFindings, load_findings

SECURITY_FIELDS = ["company", "price", "price_time", "market_cap", "shares_outstanding", "float", "avg_volume_30d",
                   "high_52w", "low_52w", "pe_ratio", "pb_ratio", "sector", "industry", "hq", "employees",
                   "listing_status", "price_12m_ago", "monthly_closes"]


def _latest_screen(settings: Settings) -> list[str]:
    briefs = sorted((settings.reports_dir / "briefs").glob("*.json"))
    if not briefs:
        return []
    doc = json.loads(briefs[-1].read_text())
    return [d["ticker"] for d in doc.get("discoveries", [])] + doc.get("need_snapshot", [])


def refresh_plan(settings: Settings, holdings: list[str], extra: list[str] | None = None, as_of: date | None = None) -> dict:
    as_of = as_of or datetime.now(timezone.utc).date()
    start = date(as_of.year - 1, as_of.month, 1)
    syms = list(dict.fromkeys([s.upper() for s in DEFAULT_WATCHLIST + holdings + _latest_screen(settings) + (extra or [])] + ["SPY"]))
    return {"symbols": syms, "batches": [syms[i:i + 10] for i in range(0, len(syms), 10)],
            "historicals": {"interval": "month", "start_time": f"{start.isoformat()}T00:00:00Z",
                            "end_time": f"{date(as_of.year, as_of.month, 1).isoformat()}T00:00:00Z"},
            "write_to": str(settings.snapshot_dir / as_of.isoformat()),
            "security_fields": SECURITY_FIELDS}


def validate_securities(doc: dict, now: datetime) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for t, r in (doc.get("securities") or {}).items():
        p = r.get("price")
        if not isinstance(p, (int, float)) or p <= 0:
            errors.append(f"{t}: invalid price {p}")
            continue
        try:
            pt = datetime.fromisoformat(str(r.get("price_time")).replace("Z", "+00:00"))
            if pt > now + timedelta(minutes=5):
                errors.append(f"{t}: price_time in the future")
        except ValueError:
            errors.append(f"{t}: unparseable price_time {r.get('price_time')}")
        closes = r.get("monthly_closes") or []
        if any((not isinstance(c, (int, float))) or c <= 0 for c in closes):
            errors.append(f"{t}: non-positive monthly close")
        if closes and abs(p / closes[-1] - 1) > 0.6:
            warnings.append(f"{t}: price {p} vs last monthly close {closes[-1]} differs >60% (verify)")
        mc, sh = r.get("market_cap"), r.get("shares_outstanding")
        if mc and sh and abs(mc / (p * sh) - 1) > 0.25:
            warnings.append(f"{t}: market_cap inconsistent with price x shares (verify)")
        if r.get("high_52w") and r.get("low_52w") and not (r["low_52w"] * 0.9 <= p <= r["high_52w"] * 1.1):
            warnings.append(f"{t}: price outside 52-week range (verify)")
    return errors, warnings


def validate_portfolio(doc: dict, now: datetime) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    pos = doc.get("positions") or {}
    port, holds = pos.get("portfolio") or {}, pos.get("holdings") or []
    if not holds:
        return ["portfolio snapshot has no holdings"], []
    for h in holds:
        if float(h.get("quantity", 0)) < 0 or float(h.get("price", 0)) <= 0:
            errors.append(f"{h.get('symbol')}: invalid quantity/price")
        if h.get("available") is not None and float(h["available"]) > float(h["quantity"]) + 1e-9:
            errors.append(f"{h['symbol']}: available > quantity")
    implied = sum(float(h["quantity"]) * float(h["price"]) for h in holds)
    eq = float(port.get("equity_value") or 0)
    if eq and abs(implied / eq - 1) > 0.03:
        errors.append(f"sum(quantity x price) ${implied:,.2f} differs >3% from broker equity_value ${eq:,.2f}")
    tv = float(port.get("total_value") or 0)
    if tv and abs((eq + float(port.get("crypto_value") or 0) + float(port.get("cash") or 0)) / tv - 1) > 0.03:
        warnings.append("equity + crypto + cash does not reconcile to total_value within 3%")
    bench = pos.get("benchmark") or {}
    if not bench.get("monthly_closes"):
        errors.append("benchmark (SPY) monthly_closes missing")
    try:
        cap = datetime.fromisoformat(doc["captured_at"].replace("Z", "+00:00"))
        if cap > now + timedelta(minutes=5):
            errors.append("captured_at in the future")
    except (KeyError, ValueError):
        errors.append("captured_at missing or invalid")
    return errors, warnings


def latest_portfolio_doc(settings: Settings) -> tuple[dict | None, Path | None]:
    best, best_p = None, None
    for p in settings.snapshot_dir.rglob("*.json"):
        d = json.loads(p.read_text())
        if "positions" in d and (best is None or d.get("captured_at", "") > best.get("captured_at", "")):
            best, best_p = d, p
    return best, best_p


def validate_day(settings: Settings, day: str, now: datetime) -> dict:
    d = settings.snapshot_dir / day
    errors, warnings = [], []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        doc = json.loads(p.read_text())
        e, w = validate_securities(doc, now)
        errors += [f"{p.name}: {x}" for x in e]
        warnings += [f"{p.name}: {x}" for x in w]
        if "positions" in doc:
            e, w = validate_portfolio(doc, now)
            errors += [f"{p.name}: {x}" for x in e]
            warnings += [f"{p.name}: {x}" for x in w]
    if not d.exists():
        errors.append(f"no snapshot directory {d}")
    return {"day": day, "errors": errors, "warnings": warnings, "ok": not errors}


def research_tasks(settings: Settings, holdings: list[str], discoveries: list[str], now: datetime,
                   max_age_days: int = 7, limit: int = 12) -> list[dict]:
    have = load_findings(settings.findings_dir)
    out, seen = [], set()
    for prio, group in ((1, holdings), (2, DEFAULT_WATCHLIST), (3, discoveries)):
        for t in group:
            t = t.upper()
            if t in seen:
                continue
            seen.add(t)
            f: AgentFindings | None = have.get(t)
            age = (now - f.researched_at).days if f else None
            if f is None or age >= max_age_days:
                out.append({"ticker": t, "priority": prio, "reason": "no research" if f is None else f"research {age}d old",
                            "output": str(settings.findings_dir / f"{t}.json")})
    return sorted(out, key=lambda x: x["priority"])[:limit]


def validate_findings_file(path: Path) -> list[str]:
    try:
        doc = AgentFindings.model_validate(json.loads(path.read_text()))
    except Exception as exc:  # noqa: BLE001
        return [f"{path.name}: {exc}"]
    errs = [f"{path.name}: finding without http(s) source" for f in doc.findings if not f.source_url.startswith("http")]
    if len(doc.findings) < 5:
        errs.append(f"{path.name}: fewer than 5 sourced findings")
    return errs
