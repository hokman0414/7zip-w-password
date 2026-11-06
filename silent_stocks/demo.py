"""Offline, fixture-based DEMO. Every company, number and source here is synthetic and labeled DEMO; it exists to
exercise the full pipeline without network access or credentials. Production connectors are unchanged."""
from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .config import Settings
from .connectors.market import SnapshotMarketConnector
from .connectors.research import AgentFindings, PolicyEvent
from .daily import state_hash, write_brief
from .db import Store
from .pipeline import Sources, analyze_universe
from .portfolio_risk import assess, propose

DEMO_URL = "https://example.com/silent-stocks-demo"


def _q_ends(n: int, last: date) -> list[tuple[date, date]]:
    out, end = [], last
    for _ in range(n):
        start = date(end.year, end.month - 2, 1)
        out.append((start, end))
        end = start - timedelta(days=1)
    return list(reversed(out))


def synthetic_facts(name: str, rev0: float, growth_q: float, gm0: float, gm_step: float, shares0: float,
                    share_growth_q: float, cash: float, opm: float, last_q: date) -> dict:
    qs = _q_ends(10, last_q)
    rev, cogs, oi, ni, cfo, capex, sh = [], [], [], [], [], [], []
    for i, (s, e) in enumerate(qs):
        filed = (e + timedelta(days=40)).isoformat()
        r = rev0 * (1 + growth_q) ** i
        gm = gm0 + gm_step * i
        base = {"start": s.isoformat(), "end": e.isoformat(), "filed": filed, "form": "10-Q", "accn": f"0000000000-26-{i:06d}"}
        rev.append(base | {"val": r})
        cogs.append(base | {"val": r * (1 - gm)})
        oi.append(base | {"val": r * (opm + 0.01 * i)})
        ni.append(base | {"val": r * (opm + 0.01 * i) * 0.8})
        cfo.append(base | {"val": r * (opm + 0.015 * i)})
        capex.append(base | {"val": r * 0.04})
        sh.append({"end": (e + timedelta(days=30)).isoformat(), "filed": filed, "form": "10-Q", "accn": base["accn"],
                   "val": shares0 * (1 + share_growth_q) ** i})
    last = qs[-1][1]
    inst = lambda v: [{"end": last.isoformat(), "filed": (last + timedelta(days=40)).isoformat(), "form": "10-Q", "accn": "0000000000-26-000009", "val": v}]
    usd = lambda rows: {"units": {"USD": rows}}
    return {"entityName": name, "facts": {
        "us-gaap": {"Revenues": usd(rev), "CostOfRevenue": usd(cogs), "OperatingIncomeLoss": usd(oi), "NetIncomeLoss": usd(ni),
                    "NetCashProvidedByUsedInOperatingActivities": usd(cfo), "PaymentsToAcquirePropertyPlantAndEquipment": usd(capex),
                    "CashAndCashEquivalentsAtCarryingValue": usd(inst(cash)), "LongTermDebt": usd(inst(cash * 0.2)),
                    "StockholdersEquity": usd(inst(cash * 3))},
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": sh}}}}}


class FixtureSec:
    def __init__(self, facts: dict[str, dict], as_of: date):
        self.facts, self.as_of = facts, as_of
        self.ciks = {t: 9_000_000 + i for i, t in enumerate(facts)}

    def cik_for(self, t):
        return self.ciks.get(t)

    def company_facts(self, cik):
        t = next(k for k, v in self.ciks.items() if v == cik)
        return self.facts[t], {"url": f"{DEMO_URL}/facts/{t}", "demo": True}

    def recent_filings(self, cik, as_of, forms=None, limit=40):
        return [{"form": "10-Q", "filed": as_of - timedelta(days=60), "accession": "0000000000-26-000009", "items": "",
                 "url": f"{DEMO_URL}/filings/{cik}", "primary_document": "demo.htm", "description": "DEMO"}]

    def full_text_search(self, *a, **k):
        return []


class NoAwards:
    def contract_awards(self, *a, **k):
        return []


def _findings(t: str, now: datetime, positive: bool) -> AgentFindings:
    s = "positive" if positive else "negative"
    claims = [("economic", "demand", f"DEMO: {t} reports record backlog"), ("technological", "product", f"DEMO: {t} launches new product"),
              ("military", "contracts", f"DEMO: {t} wins defense program award"), ("political", "policy", f"DEMO: {t} benefits from domestic sourcing rules")]
    return AgentFindings.model_validate({
        "ticker": t, "company": f"{t} Demo Corp", "researched_at": now.isoformat(), "agent_id": "demo-fixture",
        "findings": [{"dimension": d, "topic": tp, "claim": c, "evidence_type": "verified", "sentiment": s,
                      "source_url": f"{DEMO_URL}/{t}/{i}", "published_date": (now - timedelta(days=10 + i)).date().isoformat()}
                     for i, (d, tp, c) in enumerate(claims)],
        "upcoming_catalysts": [{"event": f"DEMO: {t} program milestone", "expected_date": (now + timedelta(days=150)).date().isoformat(),
                                "date_confidence": "company_guided", "source_url": f"{DEMO_URL}/{t}/cat"}],
        "policy_links": [{"country": "United States", "policy": "DEMO domestic sourcing rule", "stage": "enacted", "industry": "defense",
                          "bottleneck": "DEMO component", "revenue_mechanism": "DEMO program revenue",
                          "evidence_of_company_revenue": positive, "source_url": f"{DEMO_URL}/{t}/policy"}],
        "key_risks": [] if positive else [{"risk": f"DEMO: {t} customer concentration", "severity": "high"}],
        "going_concern_warning": False})


def run_demo(settings: Settings) -> dict:
    now = datetime.now(timezone.utc)
    tmp = Path(tempfile.mkdtemp(prefix="silent-demo-"))
    s = replace(settings, db_path=tmp / "demo.db", reports_dir=settings.reports_dir / "demo")
    snap = tmp / "snapshots"
    snap.mkdir()
    last_q = date(now.year, ((now.month - 1) // 3) * 3 + 1, 1) - timedelta(days=1)
    if (now.date() - last_q).days < 45:
        last_q = date(last_q.year, last_q.month - 2, 1) - timedelta(days=1)
    specs = {"DEMOA": dict(rev0=20e6, growth_q=0.09, gm0=0.30, gm_step=0.01, shares0=50e6, share_growth_q=0.002, cash=60e6, opm=0.02, price=12.0, positive=True),
             "DEMOB": dict(rev0=30e6, growth_q=0.06, gm0=0.25, gm_step=-0.005, shares0=80e6, share_growth_q=0.09, cash=8e6, opm=-0.25, price=3.0, positive=False)}
    facts, secs, findings = {}, {}, {}
    for t, sp in specs.items():
        facts[t] = synthetic_facts(f"{t} Demo Corp", sp["rev0"], sp["growth_q"], sp["gm0"], sp["gm_step"], sp["shares0"],
                                   sp["share_growth_q"], sp["cash"], sp["opm"], last_q)
        sh = sp["shares0"] * (1 + sp["share_growth_q"]) ** 9
        closes = [round(sp["price"] * (0.97 + 0.01 * ((i * 7) % 5)), 2) for i in range(12)]
        secs[t] = {"company": f"{t} Demo Corp", "price": sp["price"], "price_time": now.isoformat(), "market_cap": sp["price"] * sh,
                   "shares_outstanding": sh, "float": sh * 0.8, "avg_volume_30d": sh * 0.004, "high_52w": sp["price"] * 1.3,
                   "low_52w": sp["price"] * 0.7, "sector": "Electronic Technology", "industry": "Aerospace & Defense",
                   "price_12m_ago": closes[0], "monthly_closes": closes}
        findings[t] = _findings(t, now - timedelta(hours=1), sp["positive"])
    port = {"source": "demo-fixture", "demo": True, "captured_at": now.isoformat(), "positions": {
        "account_last4": "DEMO", "account_type": "cash", "option_level": None,
        "portfolio": {"total_value": 10000.0, "cash": 0.0, "crypto_value": 0.0},
        "benchmark": {"symbol": "SPY", "price": 100.0, "monthly_closes": [90, 92, 91, 94, 95, 93, 96, 97, 99, 98, 100, 101]},
        "holdings": [{"symbol": "DEMOB", "quantity": 1000, "price": 3.0, "monthly_closes": [3.5, 3.2, 3.6, 2.9, 3.3, 2.6, 3.4, 2.8, 3.1, 2.7, 3.2, 3.0]},
                     {"symbol": "DEMOETF", "quantity": 70, "price": 100.0, "asset_type": "index_etf", "monthly_closes": [90, 92, 91, 94, 95, 93, 96, 97, 99, 98, 100, 101]}]}}
    (snap / "demo.json").write_text(json.dumps({"source": "demo-fixture", "demo": True, "captured_at": now.isoformat(), "securities": secs}))
    (snap / "portfolio.json").write_text(json.dumps(port))
    market = SnapshotMarketConnector(snap, name="demo-fixture", is_demo=True)
    events = [PolicyEvent(id="demo-1", country="United States", policy="DEMO domestic sourcing rule", stage="enacted",
                          event_date=(now - timedelta(days=60)).date(), industries=["defense"], bottlenecks=["DEMO component"],
                          direction="tailwind", source_url=f"{DEMO_URL}/policy")]
    src = Sources(s, FixtureSec(facts, now.date()), NoAwards(), market, findings, events)
    run_id = f"demo-{now:%Y%m%dT%H%M%SZ}"
    reports = analyze_universe(list(specs), now, src, run_id=run_id)
    store = Store(s.db_path)
    store.start_run(run_id, now.isoformat(), now.isoformat(), "demo", len(reports))
    for r in reports:
        store.save_report(r, state_hash(r))
    by_t = {r.ticker: r for r in reports}
    risk = assess(market.positions, by_t)
    proposals = propose(risk, by_t)
    store.finish_run(run_id, datetime.now(timezone.utc).isoformat(), "DEMO fixture run")
    brief = write_brief(s, run_id, now, reports, [], [], risk, proposals, [])
    brief.write_text("> **DEMO — synthetic fixture data. Not real companies, prices or sources.**\n\n" + brief.read_text())
    return {"run_id": run_id, "reports": reports, "risk": risk, "proposals": proposals, "brief": brief, "db": s.db_path}
