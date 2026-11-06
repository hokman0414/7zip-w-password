"""Command line: screen, analyze, daily, propose-trades, schedule, api, dashboard, demo."""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_WATCHLIST, get_settings


def _sec(settings, offline=False):
    from .connectors.sec_edgar import SecEdgar
    from .http import CachedHttp
    return SecEdgar(CachedHttp(settings.cache_dir, settings.sec_user_agent, offline=offline))


def cmd_screen(a, s):
    from .discovery import enrich_and_filter, screen_universe
    sec = _sec(s, a.offline)
    rows = enrich_and_filter(sec, screen_universe(sec, datetime.now(timezone.utc).date()), limit=a.limit)
    print(f"{'ticker':7} {'period':8} {'rev_q':>14} {'yoy':>7} {'accel':>7} {'score':>6}  sic")
    for r in rows:
        acc = f"{r.acceleration:+.0%}" if r.acceleration is not None else "n/a"
        print(f"{r.ticker:7} {r.period:8} {r.revenue_q:14,.0f} {r.growth_yoy:7.0%} {acc:>7} {r.fundamental_score:6.1f}  {r.sic} {r.sic_description}")


def cmd_analyze(a, s):
    from .connectors.market import SnapshotMarketConnector
    from .connectors.usaspending import UsaSpending
    from .daily import make_executor
    from .http import CachedHttp
    from .pipeline import Sources, analyze_universe, load_research
    now = datetime.now(timezone.utc)
    http = CachedHttp(s.cache_dir, s.sec_user_agent, offline=a.offline)
    from .connectors.sec_edgar import SecEdgar
    f, p = load_research(s, now)
    src = Sources(s, SecEdgar(http), UsaSpending(http), SnapshotMarketConnector(s.snapshot_dir), f, p)
    reports = analyze_universe([t.upper() for t in a.tickers], now, src, executor=make_executor(s))
    for r in reports:
        if a.json:
            print(r.model_dump_json(indent=2))
            continue
        print_report(r, verbose=a.verbose)


def print_report(r, verbose=False):
    t, v = r.tally, r.valuation
    print(f"\n=== {r.ticker} — {r.company} — {r.status.value}")
    print(f"price {r.price} ({r.price_source}, {r.price_time}); market cap {r.market_cap or 0:,.0f}; {r.industry}")
    print(f"votes: YES {t.yes} (independent {t.independent_yes}, collapsed {t.dependent_yes}) NO {t.no} UNKNOWN {t.unknown} "
          f"completed {t.completed}/100 -> {t.gate_reason}")
    print(f"  {t.disclaimer}")
    print(f"status reason: {r.discovery_components.get('_status_reason')}")
    for x in r.vetoes:
        print(f"  [{x.severity}] {x.code}: {x.description}")
    if v.ev_revenue:
        print(f"valuation: EV ${v.enterprise_value:,.0f}, EV/rev {v.ev_revenue:.2f}x (peer {v.peer_ev_revenue_median or float('nan'):.2f}x), "
              f"revenue TTM ${v.revenue_ttm:,.0f}, growth {v.revenue_growth_yoy if v.revenue_growth_yoy is not None else float('nan'):.0%}")
        print(f"  doubling needs revenue ${v.revenue_required_to_double_at_current_multiple:,.0f} at current multiple "
              f"({v.growth_required_to_double_at_current_multiple:+.0%})")
        for sc in v.scenarios:
            print(f"  {sc.name:4}: ${sc.implied_price:,.2f} ({sc.upside_pct:+.0%}) g={sc.assumptions['revenue_growth']:.0%} "
                  f"m={sc.assumptions['ev_revenue']:.2f}x dil={sc.assumptions['dilution']:.0%}")
        if v.monte_carlo:
            mc = v.monte_carlo
            print(f"  Monte Carlo: P(>=2x) {mc.p_double:.1%}, P(<=0.5x) {mc.p_loss_50:.1%} [{mc.label}]")
    for d in r.stemple:
        print(f"  STEMPLE {d.dimension:13} {d.assessment:12} +{d.positive}/-{d.negative} ({d.verified} verified)")
    for tq in r.techniques:
        print(f"  SAT {tq.technique}: {tq.summary[:200]}")
    if verbose:
        for a in r.assignments:
            print(f"   #{a.assignment_id:3} {a.vote.value:7} {a.confidence:.2f} [{a.group}] {a.question} -> {a.finding[:160]}"
                  + (f" (dup of #{a.dependent_on})" if a.dependent_on else ""))
    print("  data gaps: " + "; ".join(r.data_gaps[:8]))


def cmd_daily(a, s):
    from .daily import run_daily
    res = run_daily(s, watchlist=a.watchlist or None, discoveries=a.top, screen_limit=a.screen_limit, offline=a.offline)
    print(Path(res["brief"]).read_text())


def cmd_propose(a, s):
    from .connectors.market import SnapshotMarketConnector
    from .db import Store
    from .portfolio_risk import assess, propose
    m = SnapshotMarketConnector(s.snapshot_dir)
    if not m.positions:
        sys.exit("no portfolio snapshot found under data/snapshots/robinhood (capture via the Robinhood MCP)")
    reports = {r.ticker: r for r in Store(s.db_path).latest_reports()}
    risk = assess(m.positions, reports)
    out = {"risk": {k: v for k, v in risk.items() if k != "holdings"},
           "holdings": [{"symbol": h.symbol, "weight": round(h.weight, 4), "vol": h.vol, "beta": h.beta,
                         "research_status": h.report_status, "critical_vetoes": h.critical_vetoes} for h in risk["holdings"]],
           "proposals": propose(risk, reports),
           "notice": "Proposals only. This system never calls place_equity_order. Review each with review_equity_order and approve manually."}
    print(json.dumps(out, indent=2, default=str))


def _holdings(s):
    from .refresh import latest_portfolio_doc
    doc, _ = latest_portfolio_doc(s)
    return [h["symbol"] for h in doc["positions"]["holdings"]] if doc else []


def cmd_refresh_plan(a, s):
    from .refresh import refresh_plan
    print(json.dumps(refresh_plan(s, _holdings(s), a.extra), indent=2))


def cmd_validate_snapshot(a, s):
    from .refresh import validate_day
    now = datetime.now(timezone.utc)
    res = validate_day(s, a.day or now.date().isoformat(), now)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["ok"] else 1)


def cmd_research_tasks(a, s):
    from .refresh import research_tasks
    briefs = sorted((s.reports_dir / "briefs").glob("*.json"))
    disc = []
    if briefs:
        doc = json.loads(briefs[-1].read_text())
        disc = [d["ticker"] for d in doc.get("discoveries", [])
                if not any(v["severity"] == "critical" for v in d.get("vetoes", []))]
    tasks = research_tasks(s, _holdings(s), disc, datetime.now(timezone.utc), a.max_age_days, a.limit)
    prompt = Path(__file__).with_name("prompts") / "research_agent.md"
    print(json.dumps({"prompt_template": str(prompt), "tasks": tasks}, indent=2))


def cmd_validate_research(a, s):
    from .refresh import validate_findings_file
    errs = [e for p in sorted(s.findings_dir.glob("*.json")) for e in validate_findings_file(p)]
    print(json.dumps({"ok": not errs, "errors": errs}, indent=2))
    sys.exit(0 if not errs else 1)


def cmd_plan_orders(a, s):
    from .execution import AutotradeConfig, load_state, plan_orders, save_state, write_plan
    from .refresh import latest_portfolio_doc, validate_portfolio
    now = datetime.now(timezone.utc)
    doc, _ = latest_portfolio_doc(s)
    if doc is None:
        sys.exit("no portfolio snapshot")
    errors, _ = validate_portfolio(doc, now)
    props_path = s.data_dir / "state" / "latest_proposals.json"
    if not props_path.exists():
        sys.exit("no proposals; run `silent-stocks daily` first")
    props = json.loads(props_path.read_text())
    if props["created_at"][:10] != now.date().isoformat():
        errors.append(f"proposals are from {props['created_at'][:10]}, not today")
    state = load_state(s)
    plan = plan_orders(AutotradeConfig.load(), s, props["proposals"], doc, errors, now, state)
    state["high_water_mark"] = plan["high_water_mark"]
    save_state(s, state)
    path = write_plan(s, plan)
    print(json.dumps(plan | {"path": str(path)}, indent=2, default=str))


def cmd_record_executions(a, s):
    from .execution import record_executions
    results = json.loads(Path(a.results).read_text())
    print(record_executions(s, results, datetime.now(timezone.utc), a.total_value))


def cmd_schedule(a, s):
    from .scheduler import serve
    serve(s)


def cmd_api(a, s):
    import uvicorn
    uvicorn.run("silent_stocks.api:app", host=a.host, port=a.port)


def cmd_dashboard(a, s):
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("dashboard.py")),
                    "--server.port", str(a.port), "--server.headless", "true"], check=False)


def cmd_demo(a, s):
    from .demo import run_demo
    res = run_demo(s)
    print(Path(res["brief"]).read_text())


def main(argv=None):
    p = argparse.ArgumentParser(prog="silent-stocks", description="Silent Stocks research platform (no order execution)")
    p.add_argument("-v", "--verbose-log", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("screen", help="SEC XBRL cross-sectional revenue-acceleration screen")
    x.add_argument("--limit", type=int, default=40)
    x.add_argument("--offline", action="store_true")
    x.set_defaults(fn=cmd_screen)
    x = sub.add_parser("analyze", help="full 100-assignment analysis for tickers")
    x.add_argument("tickers", nargs="*", default=DEFAULT_WATCHLIST)
    x.add_argument("--json", action="store_true")
    x.add_argument("--verbose", action="store_true", help="print all 100 assignment votes")
    x.add_argument("--offline", action="store_true")
    x.set_defaults(fn=cmd_analyze)
    x = sub.add_parser("daily", help="run the daily pipeline once now")
    x.add_argument("--watchlist", nargs="*")
    x.add_argument("--top", type=int, default=20)
    x.add_argument("--screen-limit", type=int, default=40)
    x.add_argument("--offline", action="store_true")
    x.set_defaults(fn=cmd_daily)
    x = sub.add_parser("propose-trades", help="portfolio risk + human-approval trade proposals")
    x.set_defaults(fn=cmd_propose)
    x = sub.add_parser("refresh-plan", help="symbols and MCP parameters for today's Robinhood snapshot refresh")
    x.add_argument("--extra", nargs="*", default=[])
    x.set_defaults(fn=cmd_refresh_plan)
    x = sub.add_parser("validate-snapshot", help="validate today's snapshot files (exit 1 on errors)")
    x.add_argument("--day")
    x.set_defaults(fn=cmd_validate_snapshot)
    x = sub.add_parser("research-tasks", help="tickers needing fresh deep research, prioritized")
    x.add_argument("--limit", type=int, default=12)
    x.add_argument("--max-age-days", type=int, default=7)
    x.set_defaults(fn=cmd_research_tasks)
    x = sub.add_parser("validate-research", help="validate research findings files (exit 1 on errors)")
    x.set_defaults(fn=cmd_validate_research)
    x = sub.add_parser("plan-orders", help="apply autotrade guardrails to today's proposals -> data/orders/<date>.json")
    x.set_defaults(fn=cmd_plan_orders)
    x = sub.add_parser("record-executions", help="store broker results for placed/skipped orders")
    x.add_argument("results")
    x.add_argument("--total-value", type=float)
    x.set_defaults(fn=cmd_record_executions)
    x = sub.add_parser("schedule", help="run the 09:00 America/New_York weekday scheduler")
    x.set_defaults(fn=cmd_schedule)
    x = sub.add_parser("api")
    x.add_argument("--host", default="127.0.0.1")
    x.add_argument("--port", type=int, default=8000)
    x.set_defaults(fn=cmd_api)
    x = sub.add_parser("dashboard")
    x.add_argument("--port", type=int, default=8501)
    x.set_defaults(fn=cmd_dashboard)
    x = sub.add_parser("demo", help="offline, fixture-based demo (labeled DEMO)")
    x.set_defaults(fn=cmd_demo)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose_log else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    a.fn(a, get_settings())


if __name__ == "__main__":
    main()
