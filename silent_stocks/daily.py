"""Daily run: screen -> analyze watchlist + discoveries -> persist -> alerts on material change -> portfolio risk
proposals -> markdown brief. Never places orders."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import DEFAULT_WATCHLIST, Settings
from .connectors.market import SnapshotMarketConnector
from .connectors.sec_edgar import SecEdgar
from .connectors.usaspending import UsaSpending
from .db import Store
from .discovery import enrich_and_filter, screen_universe
from .http import CachedHttp
from .models import CompanyReport, Status
from .pipeline import Sources, analyze_universe, load_research
from .portfolio_risk import assess, propose

log = logging.getLogger(__name__)


def make_executor(settings: Settings):
    if settings.openai_api_key and settings.llm_model:
        from .llm import LlmExecutor
        return LlmExecutor(settings.openai_api_key, settings.llm_model)
    return None


def state_hash(r: CompanyReport) -> str:
    basis = {"status": r.status.value, "iyes": r.tally.independent_yes // 5, "vetoes": sorted(v.code for v in r.vetoes),
             "gate": r.tally.passes_gate, "bull2x": r.valuation.bull_meets_double}
    return hashlib.sha1(json.dumps(basis, sort_keys=True).encode()).hexdigest()[:16]


def diff(prev: CompanyReport | None, cur: CompanyReport) -> list[tuple[str, str]]:
    if prev is None:
        return [("new", f"{cur.ticker} first analyzed: {cur.status.value}")]
    out = []
    if prev.status != cur.status:
        out.append(("status", f"{cur.ticker} status {prev.status.value} -> {cur.status.value}"))
    new_v = {v.code for v in cur.vetoes} - {v.code for v in prev.vetoes}
    gone_v = {v.code for v in prev.vetoes} - {v.code for v in cur.vetoes}
    if new_v:
        out.append(("veto", f"{cur.ticker} new risk flags: {', '.join(sorted(new_v))}"))
    if gone_v:
        out.append(("veto_cleared", f"{cur.ticker} cleared: {', '.join(sorted(gone_v))}"))
    d = cur.tally.independent_yes - prev.tally.independent_yes
    if abs(d) >= 5:
        out.append(("score", f"{cur.ticker} independent YES {prev.tally.independent_yes} -> {cur.tally.independent_yes}"))
    old_ev = {e.id for e in prev.evidence}
    fresh = [e for e in cur.evidence if e.id not in old_ev and e.provider.startswith(("research-agent", "sec-edgar-fts", "usaspending"))]
    if fresh:
        out.append(("evidence", f"{cur.ticker} {len(fresh)} new sourced items, e.g. {fresh[0].claim[:120]}"))
    return out


def run_daily(settings: Settings, watchlist: list[str] | None = None, discoveries: int = 20, screen_limit: int = 40,
              now: datetime | None = None, offline: bool = False) -> dict:
    now = now or datetime.now(timezone.utc)
    watchlist = [t.upper() for t in (watchlist or DEFAULT_WATCHLIST)]
    run_id = f"daily-{now:%Y%m%dT%H%M%SZ}"
    store = Store(settings.db_path)
    http = CachedHttp(settings.cache_dir, settings.sec_user_agent, offline=offline)
    sec, usa = SecEdgar(http), UsaSpending(http)
    market = SnapshotMarketConnector(settings.snapshot_dir)
    findings, events = load_research(settings, now)
    src = Sources(settings, sec, usa, market, findings, events)

    screen_meta: dict[str, dict] = {}
    try:
        rows = enrich_and_filter(sec, screen_universe(sec, now.date()), limit=screen_limit)
        for r in rows:
            screen_meta[r.ticker] = {"period": r.period, "revenue_q": r.revenue_q, "growth_yoy": round(r.growth_yoy, 4),
                                     "acceleration": r.acceleration, "fundamental_score": r.fundamental_score,
                                     "sic": r.sic, "sic_description": r.sic_description, "sources": r.sources[:4]}
    except Exception as exc:  # noqa: BLE001
        log.error("discovery screen failed: %s", exc)
    candidates = [t for t in screen_meta if t not in watchlist]
    need_snapshot = [t for t in candidates if market.get(t) is None]
    analyzed = watchlist + [t for t in candidates if market.get(t) is not None]
    store.start_run(run_id, now.isoformat(), now.isoformat(), "daily", len(analyzed))
    reports = analyze_universe(analyzed, now, src, discovery_meta=screen_meta, run_id=run_id, executor=make_executor(settings))

    alerts = []
    for r in reports:
        prev = store.previous_report(r.ticker, run_id)
        h = state_hash(r)
        store.save_report(r, h)
        for kind, msg in diff(prev, r):
            key = hashlib.sha1(f"{r.ticker}|{kind}|{h}|{msg if kind == 'evidence' else ''}".encode()).hexdigest()
            if store.add_alert(key, run_id, r.ticker, now.isoformat(), kind, msg):
                alerts.append({"ticker": r.ticker, "kind": kind, "message": msg})

    by_t = {r.ticker: r for r in reports}
    disc = sorted([r for r in reports if r.ticker not in watchlist], key=lambda r: r.discovery_score or 0, reverse=True)[:discoveries]
    risk, proposals = None, []
    if market.positions:
        risk = assess(market.positions, by_t)
        proposals = propose(risk, by_t)
        store.save_proposals(run_id, now.isoformat(), proposals)
    store.finish_run(run_id, datetime.now(timezone.utc).isoformat(),
                     f"{len(reports)} analyzed; {len(need_snapshot)} discoveries need a market snapshot")
    brief = write_brief(settings, run_id, now, [by_t[t] for t in watchlist if t in by_t], disc, alerts, risk, proposals, need_snapshot)
    return {"run_id": run_id, "reports": reports, "watchlist": watchlist, "discoveries": disc, "alerts": alerts,
            "risk": risk, "proposals": proposals, "need_snapshot": need_snapshot, "brief": brief}


def _row(r: CompanyReport) -> str:
    v = r.valuation
    up = next((s.upside_pct for s in v.scenarios if s.name == "bull"), None)
    vetoes = ", ".join(x.code for x in r.vetoes if x.severity == "critical") or "-"
    return (f"| {r.ticker} | {r.status.value} | {r.price if r.price is not None else 'n/a'} | {r.tally.independent_yes}/{r.tally.yes}/{r.tally.no}/{r.tally.unknown} | "
            f"{r.discovery_score if r.discovery_score is not None else 'n/a'} | {f'{v.ev_revenue:.2f}x' if v.ev_revenue else 'n/a'} | "
            f"{f'{up:+.0%}' if up is not None else 'n/a'} | {vetoes} |")


def write_brief(settings: Settings, run_id: str, now: datetime, watch: list[CompanyReport], disc: list[CompanyReport],
                alerts: list[dict], risk: dict | None, proposals: list[dict], need_snapshot: list[str]) -> Path:
    et = now.astimezone(ZoneInfo(settings.timezone))
    out_dir = settings.reports_dir / "briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{et:%Y-%m-%d}.md"
    hdr = "| Ticker | Status | Price | Indep YES / YES / NO / UNK | Discovery | EV/Rev | Bull case | Critical vetoes |\n|---|---|---|---|---|---|---|---|"
    lines = [f"# Silent Stocks daily brief — {et:%Y-%m-%d %H:%M %Z}", "", f"Run `{run_id}`. Research output only; no orders were placed.",
             "Vote counts are an evidence threshold, not a probability. 80/100 is not an 80% chance of doubling.", ""]
    q = [r for r in watch + disc if r.status == Status.QUALIFIED]
    lines += ["## Qualified", ""] + ([f"- **{r.ticker}** {r.tally.independent_yes}/100 independent YES" for r in q] or ["- None today."]) + [""]
    lines += ["## Watchlist", "", hdr] + [_row(r) for r in watch] + [""]
    lines += [f"## Top {len(disc)} discoveries", "", hdr] + [_row(r) for r in disc] + [""]
    if need_snapshot:
        lines += [f"Screened but no market snapshot (run the MCP refresh): {', '.join(need_snapshot)}", ""]
    lines += ["## Alerts (new since last run)", ""] + ([f"- [{a['kind']}] {a['message']}" for a in alerts] or ["- None."]) + [""]
    if risk:
        lines += ["## Portfolio risk", "",
                  f"- Total ${risk['total_value']:,.2f}; cash ${risk['cash']:,.2f}; beta {risk['portfolio_beta']:.2f}; "
                  f"vol {risk['portfolio_vol']:.0%}; effective positions {risk['effective_positions']:.1f}",
                  f"- Method: {risk['method']}", ""] + [f"- **{f['symbol']}** {f['flag']}: {f['detail']}" for f in risk["flags"]] + [""]
        lines += ["## Proposed actions (require human approval; nothing submitted)", ""]
        for p in proposals:
            amt = f"{p['quantity']} sh (~${p['est_value']:,.2f})" if "quantity" in p else (f"${p['dollar_amount']:,.2f}" if "dollar_amount" in p else "")
            lines.append(f"- `{p['status'].split(' ')[0]}` {p['side'].upper()} {p['symbol']} {amt}: {p['rationale']}")
        lines.append("")
    path.write_text("\n".join(lines))
    (out_dir / f"{et:%Y-%m-%d}.json").write_text(json.dumps(
        {"run_id": run_id, "alerts": alerts, "proposals": proposals,
         "watchlist": [r.model_dump(mode="json", include={"ticker", "status", "tally", "vetoes", "discovery_score"}) for r in watch],
         "discoveries": [r.model_dump(mode="json", include={"ticker", "status", "tally", "vetoes", "discovery_score"}) for r in disc]},
        indent=2, default=str))
    return path
