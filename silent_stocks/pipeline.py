"""End-to-end analysis: discover -> collect evidence -> STEMPLE/policy -> 100 assignments -> tally/vetoes ->
valuation & forecast -> structured techniques -> CompanyReport."""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from . import policy_graph, sat, stemple
from .config import Settings
from .connectors.market import MarketData
from .connectors.research import AgentFindings, PolicyEvent, load_findings, load_policy_events
from .connectors.sec_edgar import FTS_URL, SecEdgar
from .connectors.usaspending import UsaSpending
from .context import CompanyContext, finding_to_evidence, within
from .discovery import discovery_score
from .financials import Fundamentals, compute_fundamentals
from .models import Catalyst, CompanyReport, Evidence, EvidenceType, Sentiment, Vote
from .valuation import ValuationInputs, peer_median_excluding, value
from .voting import decide_status, risk_vetoes, run_assignments, tally

log = logging.getLogger(__name__)

FTS_CHECKS = {
    "substantial doubt": ["substantial doubt about our ability to continue as a going concern",
                          "substantial doubt about the company's ability to continue as a going concern"],
    "material weakness": ["identified a material weakness"],
}


@dataclass
class Sources:
    settings: Settings
    sec: SecEdgar | None
    usa: UsaSpending | None
    market: object
    findings: dict[str, AgentFindings] = field(default_factory=dict)
    policy_events: list[PolicyEvent] = field(default_factory=list)


def load_research(settings: Settings, as_of: datetime) -> tuple[dict[str, AgentFindings], list[PolicyEvent]]:
    return load_findings(settings.findings_dir, as_of), load_policy_events(settings.policy_events_path, as_of.date())


def _market_evidence(t: str, md: MarketData) -> Evidence:
    return Evidence(
        id=f"mkt:{t}", ticker=t, provider="robinhood-mcp" if not md.is_demo else "demo-fixture",
        claim=(f"{t} last ${md.price} at {md.price_time:%Y-%m-%d %H:%M}Z; market cap {md.market_cap or 0:,.0f}; "
               f"12m return {md.return_12m if md.return_12m is not None else 'n/a'}"),
        source_url=f"https://robinhood.com/us/en/stocks/{t}/", source_title=f"Robinhood MCP snapshot {md.snapshot_file}",
        published_date=md.price_time.date() if md.price_time else None,
        evidence_type=EvidenceType.VERIFIED if not md.is_demo else EvidenceType.UNSUPPORTED_HYPOTHESIS,
        metric="price", value=md.price, dimension="economic", topic="market")


def _fts(sec: SecEdgar, cik: int, as_of: date, name: str, key: str, phrases: list[str], ctx: CompanyContext) -> dict:
    start, end = as_of - timedelta(days=365), as_of
    hits: list[dict] = []
    try:
        for p in phrases:
            hits += sec.full_text_search(p, cik, start, end, forms="10-K,10-Q")
    except Exception as exc:  # noqa: BLE001 - unreachable search leaves the check UNKNOWN, never YES
        log.warning("FTS %s for %s failed: %s", key, name, exc)
        return {"ok": False, "hits": [], "hit_evidence": [], "evidence_id": None, "start": start, "end": end, "error": str(exc)}
    hits = [h for h in hits if h.get("filed") and date.fromisoformat(h["filed"]) <= as_of]
    hit_ev = [ctx.add(Evidence(ticker=ctx.ticker, claim=f"'{key}' language in {h['form']} filed {h['filed']} (verify context)",
                               source_url=h["url"] or FTS_URL, published_date=date.fromisoformat(h["filed"]),
                               evidence_type=EvidenceType.VERIFIED, provider="sec-edgar-fts", sentiment=Sentiment.NEGATIVE,
                               dimension="legal", topic=key)).id for h in hits[:5]]
    absent = ctx.add(Evidence(ticker=ctx.ticker, claim=f"SEC full-text search: no '{key}' disclosure in 10-K/10-Q filed {start}..{end}",
                              source_url=f"https://efts.sec.gov/LATEST/search-index?q=%22{phrases[0].replace(' ', '%20')}%22&ciks={cik:010d}",
                              published_date=end, evidence_type=EvidenceType.VERIFIED, provider="sec-edgar-fts",
                              dimension="legal", topic=key)).id if not hits else None
    return {"ok": True, "hits": hits, "hit_evidence": hit_ev, "evidence_id": absent, "start": start, "end": end}


def build_context(t: str, as_of: datetime, src: Sources) -> CompanyContext:
    md = src.market.get(t)
    fundamentals: Fundamentals | None = None
    cik = src.sec.cik_for(t) if src.sec else None
    company = (md.company if md else None) or t
    filings: list[dict] = []
    if src.sec and cik:
        try:
            facts, _ = src.sec.company_facts(cik)
            fundamentals = compute_fundamentals(cik, facts, as_of.date())
            company = fundamentals.name or company
        except Exception as exc:  # noqa: BLE001
            log.warning("company facts unavailable for %s: %s", t, exc)
        try:
            filings = src.sec.recent_filings(cik, as_of.date(), limit=80)
        except Exception as exc:  # noqa: BLE001
            log.warning("submissions unavailable for %s: %s", t, exc)
    findings = src.findings.get(t)
    ctx = CompanyContext(ticker=t, company=company, as_of=as_of, market=md, fundamentals=fundamentals, valuation=None,
                         findings=findings, policy_events=src.policy_events, policy_chains=[], contracts=[],
                         filings=filings, filing_searches={}, industries=set())
    if fundamentals:
        for e in fundamentals.evidence.values():
            ctx.add(e)
    if md and md.price is not None:
        ctx.add(_market_evidence(t, md))
    if findings:
        for f in findings.findings:
            raw = f.model_dump(mode="json")
            ctx.finding_ev.append((ctx.add(finding_to_evidence(t, raw, f"research-agent:{findings.agent_id}")), raw))
    if filings and cik:
        idx = ctx.add(Evidence(ticker=t, claim=f"SEC EDGAR filing index for {company}: {len(filings)} filings through {as_of.date()}",
                               source_url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=include&count=40",
                               published_date=filings[0]["filed"], evidence_type=EvidenceType.VERIFIED, provider="sec-submissions",
                               dimension="legal", topic="filings"))
        ctx.filing_searches["_filings_index"] = {"ok": True, "hits": [], "hit_evidence": [], "evidence_id": idx.id}
        nr = [f for f in filings if f["form"] == "8-K" and "4.02" in (f.get("items") or "") and within(f["filed"], as_of.date(), 365)]
        nr_ev = [ctx.add(Evidence(ticker=t, claim=f"8-K Item 4.02 non-reliance filed {f['filed']}", source_url=f["url"],
                                  published_date=f["filed"], evidence_type=EvidenceType.VERIFIED, provider="sec-submissions",
                                  sentiment=Sentiment.NEGATIVE, dimension="legal", topic="restatement")).id for f in nr]
        ctx.filing_searches["non-reliance"] = {"ok": True, "hits": nr, "hit_evidence": nr_ev,
                                               "evidence_id": None if nr else idx.id,
                                               "start": as_of.date() - timedelta(days=365), "end": as_of.date()}
    if src.sec and cik:
        for key, phrases in FTS_CHECKS.items():
            ctx.filing_searches[key] = _fts(src.sec, cik, as_of.date(), company, key, phrases, ctx)
    if src.usa and company:
        try:
            awards = src.usa.contract_awards(company, as_of.date())
        except Exception as exc:  # noqa: BLE001
            log.warning("USAspending unavailable for %s: %s", t, exc)
            awards = []
        for a in awards:
            a["evidence_id"] = ctx.add(Evidence(
                ticker=t, claim=f"Federal contract {a['award_id']} {a['agency']} ${a['amount']:,.0f} to '{a['recipient']}' (name-matched; verify recipient)",
                source_url=a["url"], published_date=date.fromisoformat(a["start_date"][:10]) if a.get("start_date") else None,
                evidence_type=EvidenceType.ANALYST_JUDGMENT, provider="usaspending", sentiment=Sentiment.POSITIVE,
                metric="award_amount", value=a["amount"], dimension="military", topic="contracts")).id
        ctx.contracts = awards
    ctx.industries = policy_graph.company_industries(md.industry if md else None, findings)
    ctx.policy_chains = policy_graph.build_chains(t, findings, src.policy_events, lambda ev: ctx.add(ev).id)
    return ctx


def _inputs(ctx: CompanyContext) -> ValuationInputs:
    m = ctx.fundamentals.metrics if ctx.fundamentals else {}
    md = ctx.market
    return ValuationInputs(
        ticker=ctx.ticker, price=md.price if md else None, price_time=md.price_time if md else None,
        market_cap=md.market_cap if md else None, shares_outstanding=m.get("shares_outstanding") or (md.shares_outstanding if md else None),
        diluted_shares=m.get("diluted_shares"), cash=m.get("cash"), debt=m.get("debt"), revenue_ttm=m.get("revenue_ttm"),
        revenue_growth=m.get("revenue_growth_yoy"), gross_margin=m.get("gross_margin"), operating_margin=m.get("operating_margin"),
        ebitda_ttm=m.get("ebitda_ttm"), fcf_ttm=m.get("fcf_ttm"), net_income_ttm=m.get("net_income_ttm"),
        dilution_yoy=m.get("dilution_yoy"), backlog=m.get("backlog"), backlog_growth=m.get("backlog_growth_yoy"),
        peer_group=md.sector if md else None, volatility_annual=md.annual_volatility if md else None,
        return_12m=md.return_12m if md else None)


def _catalysts(ctx: CompanyContext) -> list[Catalyst]:
    out = []
    for c in (ctx.findings.upcoming_catalysts if ctx.findings else []):
        w = None
        if c.expected_date:
            days = (c.expected_date - ctx.as_of.date()).days
            w = 90 <= days <= 365
        out.append(Catalyst(event=c.event, expected_date=c.expected_date, date_confidence=c.date_confidence,
                            source_url=c.source_url, within_3_12_months=w))
    return out


def analyze_universe(tickers: list[str], as_of: datetime, src: Sources, discovery_meta: dict[str, dict] | None = None,
                     run_id: str | None = None, executor=None) -> list[CompanyReport]:
    run_id = run_id or f"run-{as_of:%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
    s = src.settings
    ctxs = {}
    for t in tickers:
        try:
            ctxs[t] = build_context(t, as_of, src)
        except Exception:  # noqa: BLE001
            log.exception("context build failed for %s", t)
    # Pass 1: own multiples for peer medians; pass 2: peer-relative valuation excluding the company itself.
    own = {}
    for t, ctx in ctxs.items():
        v0 = value(_inputs(ctx), mc_sims=200)
        own[t] = (ctx.market.sector if ctx.market else None, v0.ev_revenue)
    reports = []
    for t, ctx in ctxs.items():
        vi = _inputs(ctx)
        vi.peer_ev_revenue_median = peer_median_excluding(t, vi.peer_group, own)
        val = value(vi)
        ctx.valuation = val
        if val.ev_revenue is not None:
            ctx.add(Evidence(id=f"val:{t}", ticker=t, provider="valuation-engine", source_url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ctx.fundamentals.cik if ctx.fundamentals else ''}",
                             source_title="Computed from SEC XBRL + Robinhood market data",
                             claim=(f"EV/revenue {val.ev_revenue:.2f}x vs peer median {val.peer_ev_revenue_median or float('nan'):.2f}x; "
                                    f"revenue growth required to double at current multiple {val.growth_required_to_double_at_current_multiple or 0:.0%}"),
                             evidence_type=EvidenceType.ANALYST_JUDGMENT, metric="ev_revenue", value=val.ev_revenue,
                             dimension="economic", topic="valuation", published_date=as_of.date()))
        results = run_assignments(ctx, executor=executor)
        tl = tally(results, s.gate_yes_threshold, s.total_assignments)
        vetoes = risk_vetoes(ctx, as_of, s.stale_market_hours)
        techniques = sat.run_all(ctx, results, vetoes, val, s.data_dir / "calibration" / "base_rates.json")
        red = next(x for x in techniques if x.technique == "Red Team Analysis")
        research_stale = bool(ctx.findings and (as_of - ctx.findings.researched_at).days > s.stale_research_days)
        status, reason = decide_status(tl, vetoes, val.bull_meets_double, ctx.findings is not None, research_stale,
                                       red.details.get("survives", False))
        cats = _catalysts(ctx)
        md, m = ctx.market, (ctx.fundamentals.metrics if ctx.fundamentals else {})
        awards = sum(a["amount"] for a in ctx.contracts)
        ds = discovery_score(
            market_cap=md.market_cap if md else None, turnover_daily=md.turnover_daily if md else None,
            return_12m=md.return_12m if md else None,
            pct_below_52w_high=(1 - md.price / md.high_52w) if md and md.price and md.high_52w else None,
            ev_revenue=val.ev_revenue, revenue_growth=m.get("revenue_growth_yoy"), acceleration=m.get("revenue_acceleration"),
            margin_change=m.get("gross_margin_change"),
            fcf_change_positive=None if m.get("fcf_change") is None else m["fcf_change"] > 0,
            dated_catalysts_3_12m=sum(1 for c in cats if c.within_3_12_months) if ctx.findings else None,
            gov_award_value_to_revenue=awards / m["revenue_ttm"] if m.get("revenue_ttm") else None,
            verified_policy_links=sum(c.evidence_of_company_revenue for c in ctx.policy_chains) if ctx.findings else None,
            news_items_90d=len(set(e.source_url for e, _ in ctx.finding_ev if within(e.published_date, as_of.date(), 90))) if ctx.findings else None)
        comps = dict(ds.components) | {"_missing": ds.missing, "_label": ds.label, "_status_reason": reason,
                                       **({"_screen": discovery_meta[t]} if discovery_meta and t in discovery_meta else {})}
        yes_sorted = sorted([r for r in results if r.vote == Vote.YES], key=lambda r: r.confidence, reverse=True)
        pos_ver = [e for e, r in ctx.finding_ev if r["sentiment"] == "positive" and r["evidence_type"] == "verified"]
        could_double = [f"{r.question} — {r.finding}" for r in yes_sorted if r.group in ("company_financial", "valuation_mispricing", "catalyst_alternative")][:5]
        could_double += [f"{e.claim} ({e.source_url})" for e in pos_ver[:3]]
        bull = next((x for x in val.scenarios if x.name == "bull"), None)
        if bull and bull.upside_pct is not None:
            could_double.append(f"Bull scenario implies {bull.upside_pct:+.0%} (growth {bull.assumptions['revenue_growth']:.0%}, {bull.assumptions['ev_revenue']:.2f}x EV/revenue)")
        pm = next(x for x in techniques if x.technique == "Premortem Analysis")
        sp = next(x for x in techniques if x.technique == "Indicators and Signposts")
        gaps = list(ctx.fundamentals.gaps if ctx.fundamentals else ["no SEC XBRL fundamentals"])
        gaps += [f"valuation: {n}" for n in val.notes]
        gaps += [f"{k}: search unavailable" for k, v in ctx.filing_searches.items() if not v.get("ok")]
        if not ctx.findings:
            gaps.append("no web research findings for this ticker; findings/catalyst/policy assignments abstain (UNKNOWN)")
        if md is None:
            gaps.append("no market data snapshot")
        regions = sorted({r for d in stemple.assess(ctx) for r in d.regions})
        reports.append(CompanyReport(
            run_id=run_id, as_of=as_of, ticker=t, company=ctx.company, status=status,
            price=md.price if md else None, price_source=md.source if md else None, price_time=md.price_time if md else None,
            market_cap=md.market_cap if md else None, industry=md.industry if md else None, country_exposure=regions,
            discovery_score=ds.score, discovery_components=comps, stemple=stemple.assess(ctx), tally=tl,
            assignments=results, vetoes=vetoes, catalysts=cats, policy_chains=ctx.policy_chains, valuation=val,
            techniques=techniques, reasons_could_double=could_double, reasons_could_fail=pm.details.get("failure_causes", []),
            leading_indicators=[f"{x['indicator']}: now {x['current']}; bullish if {x['bullish_if']}, bearish if {x['bearish_if']}" for x in sp.details["signposts"]],
            evidence=list(ctx.evidence.values()), data_gaps=gaps))
    return reports


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
