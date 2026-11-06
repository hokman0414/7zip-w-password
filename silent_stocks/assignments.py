"""The 100 analytical assignments.

Each assignment has a unique question, a narrow responsibility, a declared evidence slice (enforced by SliceView),
a falsification condition, and a deterministic evaluator. Every question is phrased so YES supports the 12-month
thesis. Missing evidence yields UNKNOWN, never YES. Evaluators are rule-based and are labeled as such in the
execution log; an optional LLM executor (llm.py) can replace them when credentials are configured.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Callable

from .context import SliceView, domain, within
from .models import AssignmentSpec, Vote

GROUPS = {
    "macro_policy": 15, "company_financial": 15, "technology_competitive": 15, "valuation_mispricing": 15,
    "military_geopolitical": 10, "supply_chain_industrial": 10, "risk_forensic": 10, "catalyst_alternative": 10,
}


@dataclass
class Outcome:
    vote: Vote
    confidence: float
    finding: str
    support: list[str]
    contra: list[str]


Evaluator = Callable[[SliceView], Outcome]


def unknown(reason: str) -> Outcome:
    return Outcome(Vote.UNKNOWN, 0.0, reason, [], [])


OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt}


def m_thresh(metric: str, op: str, thr: float, label: str, pct: bool = True) -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        val = v.fin(metric)
        if val is None:
            return unknown(f"{label}: metric '{metric}' unavailable in point-in-time SEC data")
        eid = v.fin_ev(metric)
        ok = OPS[op](val, thr)
        shown = f"{val:.1%}" if pct else f"{val:,.2f}"
        need = f"{thr:.0%}" if pct else f"{thr:,.2f}"
        return Outcome(Vote.YES if ok else Vote.NO, 0.8, f"{label}: {shown} (test {op} {need})",
                       [eid] if ok and eid else [], [eid] if not ok and eid else [])
    return ev


def _verified(rows, sentiment: str):
    return [e for e, r in rows if r["evidence_type"] == "verified" and r["sentiment"] == sentiment]


def f_pos(label: str, dims=None, topics=None, keywords=(), min_pos=1, max_age=None) -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        if v.raw_findings() is None:
            return unknown(f"{label}: no research-agent findings for this company")
        rows = v.findings(dims, topics, keywords, max_age)
        pos, neg = _verified(rows, "positive"), _verified(rows, "negative")
        if len(pos) >= min_pos and len(pos) > len(neg):
            return Outcome(Vote.YES, min(0.5 + 0.1 * len(pos), 0.8), f"{label}: {len(pos)} verified positive vs {len(neg)} verified negative",
                           [v.register(e) for e in pos], [v.register(e) for e in neg])
        if neg and len(neg) >= len(pos):
            return Outcome(Vote.NO, min(0.5 + 0.1 * len(neg), 0.8), f"{label}: {len(neg)} verified negative vs {len(pos)} verified positive",
                           [v.register(e) for e in pos], [v.register(e) for e in neg])
        return unknown(f"{label}: insufficient verified evidence ({len(rows)} related findings)")
    return ev


def f_no_neg(label: str, dims=None, topics=None, keywords=()) -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        if v.raw_findings() is None:
            return unknown(f"{label}: no research-agent findings for this company")
        rows = v.findings(dims, topics, keywords)
        neg = _verified(rows, "negative")
        if neg:
            return Outcome(Vote.NO, 0.7, f"{label}: {len(neg)} verified adverse finding(s)", [], [v.register(e) for e in neg])
        examined = [e for e, r in rows if r["evidence_type"] == "verified"]
        if not examined:
            return unknown(f"{label}: no verified evidence examined in this domain")
        return Outcome(Vote.YES, 0.55, f"{label}: {len(examined)} verified finding(s) examined, none adverse",
                       [v.register(e) for e in examined], [])
    return ev


def chain_rule(label: str, pred: Callable, require_revenue: bool = True) -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        chains = v.chains()
        company_chains = [c for c in chains if c.company == v.ticker]
        if not company_chains:
            return unknown(f"{label}: no company-specific policy linkage evidenced")
        hits = [c for c in company_chains if pred(c) and (c.evidence_of_company_revenue or not require_revenue)]
        if hits:
            ids = sorted({i for c in hits for i in c.evidence_ids})
            return Outcome(Vote.YES, 0.6, f"{label}: {len(hits)} evidenced chain(s), e.g. {hits[0].country} / {hits[0].policy[:80]}", ids, [])
        return Outcome(Vote.NO, 0.5, f"{label}: {len(company_chains)} linkage(s) exist but none satisfy this test", [],
                       sorted({i for c in company_chains for i in c.evidence_ids})[:3])
    return ev


def fts_absent(key: str, label: str) -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        res = v.filing_search(key)
        if not res or not res.get("ok"):
            return unknown(f"{label}: SEC full-text search unavailable")
        if res["hits"]:
            return Outcome(Vote.NO, 0.75, f"{label}: phrase found in {len(res['hits'])} filing(s)", [], res["hit_evidence"])
        return Outcome(Vote.YES, 0.7, f"{label}: no matches in filings {res['start']}..{res['end']}", [res["evidence_id"]], [])
    return ev


def val_rule(label: str, getter: Callable, op: str, thr: float, fmt: str = "{:.1%}") -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        val = v.val()
        x = getter(val) if val else None
        if x is None:
            return unknown(f"{label}: valuation input unavailable")
        ok = OPS[op](x, thr)
        eid = v.val_ev()
        return Outcome(Vote.YES if ok else Vote.NO, 0.6, f"{label}: {fmt.format(x)} (test {op} {fmt.format(thr)})",
                       [eid] if ok and eid else [], [eid] if not ok and eid else [])
    return ev


def mkt_rule(label: str, getter: Callable, op: str, thr: float, fmt: str = "{:.1%}") -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        md = v.mkt()
        x = getter(md) if md else None
        if x is None:
            return unknown(f"{label}: market data field unavailable")
        ok = OPS[op](x, thr)
        eid = v.mkt_ev()
        return Outcome(Vote.YES if ok else Vote.NO, 0.7, f"{label}: {fmt.format(x)} (test {op} {fmt.format(thr)})",
                       [eid] if ok and eid else [], [eid] if not ok and eid else [])
    return ev


# ---------- bespoke evaluators ----------

def _country_in(names):
    names = {n.lower() for n in names}
    return lambda c: any(n in c.country.lower() for n in names)


ACTIVE_STAGES = {"enacted", "implementation", "enforcement"}
DEFENSE_TAGS = ("defense", "drone", "counter", "military", "shipbuild", "sonar", "missile", "munition", "nato")


def headwind_absent(v: SliceView) -> Outcome:
    inds = v.industries()
    if not inds:
        return unknown("Industry tags unknown; cannot test for policy headwinds")
    events = v.policy_events()
    head = [e for e in events if e.direction == "headwind" and set(e.industries) & inds and e.stage in ACTIVE_STAGES]
    tail = [e for e in events if e.direction == "tailwind" and set(e.industries) & inds and e.stage in ACTIVE_STAGES]
    if not events:
        return unknown("No policy events loaded")
    ids = []
    for e in head + tail:
        from .models import Evidence, EvidenceType
        ids.append(v.register(Evidence(claim=f"{e.country}: {e.policy} ({e.stage})", source_url=e.source_url,
                                       source_title=e.source_title, published_date=e.event_date,
                                       evidence_type=EvidenceType.VERIFIED, provider="policy-research")))
    head_ids, tail_ids = ids[: len(head)], ids[len(head):]
    if head and len(head) >= len(tail):
        return Outcome(Vote.NO, 0.5, f"{len(head)} active headwind vs {len(tail)} tailwind policies for {sorted(inds)}", tail_ids, head_ids)
    if tail:
        return Outcome(Vote.YES, 0.5, f"{len(tail)} active tailwind vs {len(head)} headwind policies for {sorted(inds)}", tail_ids, head_ids)
    return unknown(f"No active policies tagged to {sorted(inds)}")


def policy_durable(v: SliceView) -> Outcome:
    chains = [c for c in v.chains() if c.company == v.ticker and c.evidence_of_company_revenue]
    if not chains:
        return unknown("No revenue-evidenced policy chain to test for durability")
    events = {e.policy.lower(): e for e in v.policy_events()}
    horizon = v.as_of.date().toordinal() + 365
    fragile = []
    for c in chains:
        if c.stage in ("expired", "reversed", "proposal"):
            fragile.append(c)
        e = events.get(c.policy.lower())
        if e and e.expiration_date and e.expiration_date.toordinal() < horizon:
            fragile.append(c)
    ids = sorted({i for c in chains for i in c.evidence_ids})
    if len(fragile) >= len(chains):
        return Outcome(Vote.NO, 0.5, "All evidenced policy linkages are proposals, reversed, or expire within 12 months", [], ids)
    return Outcome(Vote.YES, 0.5, f"{len(chains) - len(fragile)} of {len(chains)} linkages are active beyond 12 months", ids, [])


def rate_sensitivity(v: SliceView) -> Outcome:
    cash, debt, ebitda = v.fin("cash"), v.fin("debt"), v.fin("ebitda_ttm")
    if cash is None or debt is None:
        return unknown("Cash or debt unavailable")
    ids = [i for i in (v.fin_ev("cash"), v.fin_ev("debt")) if i]
    if cash >= debt:
        return Outcome(Vote.YES, 0.75, f"Net cash ${cash - debt:,.0f}: limited refinancing-rate exposure", ids, [])
    nd = debt - cash
    if ebitda and ebitda > 0 and nd / ebitda <= 3:
        return Outcome(Vote.YES, 0.6, f"Net debt/EBITDA {nd / ebitda:.1f}x (<=3x)", ids, [])
    return Outcome(Vote.NO, 0.7, f"Net debt ${nd:,.0f} with EBITDA {ebitda if ebitda is not None else 'n/a'}: rate-sensitive", [], ids)


def runway_ok(v: SliceView) -> Outcome:
    fcf, runway = v.fin("fcf_ttm"), v.fin("cash_runway_months")
    if fcf is None:
        return unknown("TTM free cash flow unavailable")
    if fcf >= 0:
        return Outcome(Vote.YES, 0.8, "Free cash flow positive: no funding runway constraint", [v.fin_ev("fcf_ttm")], [])
    if runway is None:
        return unknown("Cash burn present but cash unavailable")
    eid = v.fin_ev("cash_runway_months")
    if runway >= 24:
        return Outcome(Vote.YES, 0.7, f"Runway ~{runway:.0f} months at TTM burn", [eid], [])
    return Outcome(Vote.NO, 0.8, f"Runway ~{runway:.0f} months (<24): financing likely within thesis window", [], [eid])


def net_cash(v: SliceView) -> Outcome:
    cash, debt = v.fin("cash"), v.fin("debt")
    if cash is None or debt is None:
        return unknown("Cash or debt unavailable")
    ids = [i for i in (v.fin_ev("cash"), v.fin_ev("debt")) if i]
    return Outcome(Vote.YES if cash > debt else Vote.NO, 0.75, f"Cash ${cash:,.0f} vs debt ${debt:,.0f}",
                   ids if cash > debt else [], [] if cash > debt else ids)


def sbc_ratio(v: SliceView) -> Outcome:
    sbc, rev = v.fin("sbc_ttm"), v.fin("revenue_ttm")
    if sbc is None or not rev:
        return unknown("Stock compensation or revenue unavailable")
    r = sbc / rev
    ids = [i for i in (v.fin_ev("sbc_ttm"), v.fin_ev("revenue_ttm")) if i]
    return Outcome(Vote.YES if r <= 0.10 else Vote.NO, 0.75, f"SBC/revenue {r:.1%} (test <= 10%)", ids if r <= 0.10 else [], [] if r <= 0.10 else ids)


def rd_intensity(v: SliceView) -> Outcome:
    rd, rev = v.fin("rd_ttm"), v.fin("revenue_ttm")
    if rd is None or not rev:
        return unknown("R&D expense not tagged or revenue unavailable")
    r = rd / rev
    ok = 0.03 <= r <= 0.35
    ids = [i for i in (v.fin_ev("rd_ttm"), v.fin_ev("revenue_ttm")) if i]
    return Outcome(Vote.YES if ok else Vote.NO, 0.6, f"R&D/revenue {r:.1%} (test 3%-35%: investing without unsustainable burn)",
                   ids if ok else [], [] if ok else ids)


def rev_per_employee(v: SliceView) -> Outcome:
    md = v.mkt()
    rev = v.fin("revenue_ttm")
    if not md or not md.employees or not rev:
        return unknown("Employee count or revenue unavailable")
    rpe = rev / md.employees
    ids = [i for i in (v.fin_ev("revenue_ttm"), v.mkt_ev()) if i]
    ok = rpe >= 250_000
    return Outcome(Vote.YES if ok else Vote.NO, 0.5, f"Revenue per employee ${rpe:,.0f} (test >= $250k)", ids if ok else [], [] if ok else ids)


def multi_source(v: SliceView) -> Outcome:
    if v.raw_findings() is None:
        return unknown("No research findings")
    rows = v.findings({"technological"}, None)
    pos = [e for e, r in rows if r["sentiment"] == "positive" and r["evidence_type"] == "verified"]
    doms = {domain(e.source_url) for e in pos}
    if len(doms) >= 2:
        return Outcome(Vote.YES, 0.6, f"Technology claims corroborated across {len(doms)} independent domains", [v.register(e) for e in pos], [])
    if pos:
        return Outcome(Vote.NO, 0.4, "Technology claims rest on a single source domain", [], [v.register(e) for e in pos])
    return unknown("No verified positive technology claims to corroborate")


def bottleneck(v: SliceView) -> Outcome:
    chains = [c for c in v.chains() if c.company == v.ticker]
    if not chains:
        return unknown("No company policy linkages")
    hits = [c for c in chains if c.bottleneck and c.evidence_of_company_revenue]
    if hits:
        return Outcome(Vote.YES, 0.55, f"Sourced bottleneck position: {hits[0].bottleneck[:90]}", sorted({i for c in hits for i in c.evidence_ids}), [])
    return Outcome(Vote.NO, 0.4, "Linkages exist but none tie a bottleneck to company revenue", [], sorted({i for c in chains for i in c.evidence_ids})[:3])


def awards_any(v: SliceView) -> Outcome:
    awards = v.contracts()
    if awards is None:
        return unknown("USAspending unavailable")
    if not awards:
        return Outcome(Vote.NO, 0.4, "No name-matched federal contract awards in the last 12 months", [], [])
    ids = [a["evidence_id"] for a in awards if a.get("evidence_id")]
    total = sum(a["amount"] for a in awards)
    return Outcome(Vote.YES, 0.55, f"{len(awards)} name-matched federal awards totaling ${total:,.0f} (verify recipient)", ids[:10], [])


def awards_material(v: SliceView) -> Outcome:
    awards, rev = v.contracts(), v.fin("revenue_ttm")
    if not rev:
        return unknown("Revenue unavailable")
    total = sum(a["amount"] for a in awards)
    ids = [a["evidence_id"] for a in awards if a.get("evidence_id")]
    r = total / rev
    ok = r >= 0.05
    return Outcome(Vote.YES if ok else Vote.NO, 0.5, f"Federal awards / TTM revenue = {r:.1%} (test >= 5%)",
                   (ids[:10] + [v.fin_ev("revenue_ttm")]) if ok else [], [] if ok else [v.fin_ev("revenue_ttm")])


def award_recent(v: SliceView) -> Outcome:
    from datetime import date
    awards = v.contracts()
    recent = [a for a in awards if a.get("start_date") and within(date.fromisoformat(a["start_date"][:10]), v.as_of.date(), 120)]
    rows = v.findings(None, {"contract"}, (), 120)
    pos = _verified(rows, "positive")
    ids = [a["evidence_id"] for a in recent if a.get("evidence_id")] + [v.register(e) for e in pos]
    if ids:
        return Outcome(Vote.YES, 0.55, f"{len(recent)} award(s) and {len(pos)} verified contract finding(s) in last 120 days", ids, [])
    if v.raw_findings() is None and not awards:
        return unknown("No contract data or findings")
    return Outcome(Vote.NO, 0.4, "No contract award evidence within 120 days", [], [])


def dual_use(v: SliceView) -> Outcome:
    if v.raw_findings() is None:
        return unknown("No research findings")
    mil = _verified(v.findings({"military"}), "positive")
    com = _verified([r for r in v.findings() if r[1]["dimension"] != "military"], "positive")
    if mil and com:
        return Outcome(Vote.YES, 0.55, f"Both military ({len(mil)}) and commercial ({len(com)}) verified demand evidence",
                       [v.register(e) for e in (mil[:2] + com[:2])], [])
    if not mil:
        return unknown("No verified military demand evidence")
    return Outcome(Vote.NO, 0.4, "Demand evidence is single-market", [], [])


def china_exposure(v: SliceView) -> Outcome:
    if v.raw_findings() is None:
        return unknown("No research findings")
    rows = v.findings(None, None, ("china", "chinese", "export control", "tariff"))
    neg = _verified(rows, "negative")
    if neg:
        return Outcome(Vote.NO, 0.6, f"{len(neg)} verified China/export-control/tariff headwind(s)", [], [v.register(e) for e in neg])
    if rows:
        return Outcome(Vote.YES, 0.45, "China/trade exposure examined; no verified headwind", [v.register(e) for e, _ in rows], [])
    return unknown("No China/trade-exposure evidence examined")


def inventory_discipline(v: SliceView) -> Outcome:
    ig, rg = v.fin("inventory_growth"), v.fin("revenue_growth_yoy")
    if ig is None or rg is None:
        return unknown("Inventory or revenue growth unavailable")
    ok = ig <= rg + 0.10
    ids = [i for i in (v.fin_ev("inventory_growth"), v.fin_ev("revenue_growth_yoy")) if i]
    return Outcome(Vote.YES if ok else Vote.NO, 0.6, f"Inventory growth {ig:.1%} vs revenue growth {rg:.1%}", ids if ok else [], [] if ok else ids)


def capex_rising(v: SliceView) -> Outcome:
    g = v.fin("capex_growth")
    if g is None:
        return unknown("Capex history unavailable")
    eid = v.fin_ev("capex_growth")
    ok = g > 0.0
    return Outcome(Vote.YES if ok else Vote.NO, 0.5, f"Capex changed {g:+.1%} YoY (capacity investment signal)", [eid] if ok else [], [] if ok else [eid])


def diversified_customers(v: SliceView) -> Outcome:
    if v.raw_findings() is None:
        return unknown("No research findings")
    rows = v.findings(None, {"customer"})
    neg = [e for e, r in rows if r["sentiment"] == "negative" and "concentrat" in r["claim"].lower()]
    pos = _verified(rows, "positive")
    if neg:
        return Outcome(Vote.NO, 0.6, "Customer concentration flagged", [], [v.register(e) for e in neg])
    if len(pos) >= 2:
        return Outcome(Vote.YES, 0.5, f"{len(pos)} distinct verified customer wins, no concentration flag", [v.register(e) for e in pos], [])
    return unknown("Insufficient customer evidence")


def cash_conversion(v: SliceView) -> Outcome:
    cfo, ebitda = v.fin("cfo_ttm"), v.fin("ebitda_ttm")
    if cfo is None or ebitda is None:
        return unknown("CFO or EBITDA unavailable")
    ids = [i for i in (v.fin_ev("cfo_ttm"), v.fin_ev("ebitda_ttm")) if i]
    ok = cfo > 0 and (ebitda <= 0 or cfo >= 0.5 * ebitda)
    return Outcome(Vote.YES if ok else Vote.NO, 0.65, f"CFO ${cfo:,.0f} vs EBITDA ${ebitda:,.0f}", ids if ok else [], [] if ok else ids)


def accruals(v: SliceView) -> Outcome:
    cfo, ni = v.fin("cfo_ttm"), v.fin("net_income_ttm")
    if cfo is None or ni is None:
        return unknown("CFO or net income unavailable")
    ids = [i for i in (v.fin_ev("cfo_ttm"), v.fin_ev("net_income_ttm")) if i]
    ok = cfo >= ni
    return Outcome(Vote.YES if ok else Vote.NO, 0.65, f"CFO ${cfo:,.0f} vs net income ${ni:,.0f} (earnings backed by cash: {ok})",
                   ids if ok else [], [] if ok else ids)


def going_concern(v: SliceView) -> Outcome:
    flag = v.going_concern_flag()
    res = v.filing_search("substantial doubt")
    if flag:
        return Outcome(Vote.NO, 0.8, "Research agent reports going-concern warning", [], res["hit_evidence"] if res else [])
    return fts_absent("substantial doubt", "Going-concern language")(v)


def dilution_events(v: SliceView) -> Outcome:
    events, dil = v.dilution_events(), v.fin("dilution_yoy")
    if events:
        ids = []
        from .models import Evidence, EvidenceType
        for e in events:
            if e.source_url:
                ids.append(v.register(Evidence(claim=e.description, source_url=e.source_url, published_date=e.date,
                                               evidence_type=EvidenceType.VERIFIED, provider="research-agent")))
        return Outcome(Vote.NO, 0.75, f"{len(events)} dilution event(s) in last 12 months", [], ids)
    if dil is None:
        return unknown("No dilution data")
    eid = v.fin_ev("dilution_yoy")
    ok = dil <= 0.05 and v.raw_findings() is not None
    if ok:
        return Outcome(Vote.YES, 0.6, f"No reported dilution events; share count {dil:+.1%}", [eid], [])
    return Outcome(Vote.NO if dil > 0.05 else Vote.UNKNOWN, 0.6 if dil > 0.05 else 0.0,
                   f"Share count {dil:+.1%} YoY", [], [eid] if dil > 0.05 else [])


def leverage(v: SliceView) -> Outcome:
    cash, debt, ebitda = v.fin("cash"), v.fin("debt"), v.fin("ebitda_ttm")
    if cash is None or debt is None:
        return unknown("Cash or debt unavailable")
    ids = [i for i in (v.fin_ev("debt"), v.fin_ev("ebitda_ttm")) if i]
    if debt <= cash:
        return Outcome(Vote.YES, 0.75, "Net cash", ids, [])
    if ebitda and ebitda > 0 and debt / ebitda <= 3:
        return Outcome(Vote.YES, 0.7, f"Debt/EBITDA {debt / ebitda:.1f}x", ids, [])
    return Outcome(Vote.NO, 0.75, "Debt exceeds 3x EBITDA (or EBITDA negative) with net debt", [], ids)


def listing_ok(v: SliceView) -> Outcome:
    md = v.mkt()
    if not md or md.price is None:
        return unknown("No market data")
    eid = v.mkt_ev()
    bad = (md.listing_status or "").lower() == "noncompliant" or md.price < 1.0
    return Outcome(Vote.NO if bad else Vote.YES, 0.8, f"Listing status {md.listing_status or 'compliant'}, price ${md.price}",
                   [] if bad else [eid], [eid] if bad else [])


def late_filings(v: SliceView) -> Outcome:
    filings = v.filings()
    if not filings:
        return unknown("Filing index unavailable")
    late = [f for f in filings if f["form"].startswith("NT ") and within(f["filed"], v.as_of.date(), 365)]
    ev_id = v.filing_search("_filings_index")
    if late:
        return Outcome(Vote.NO, 0.8, f"{len(late)} late-filing notice(s) (NT 10-K/10-Q) in last 12 months", [], [ev_id["evidence_id"]] if ev_id else [])
    return Outcome(Vote.YES, 0.7, "No late-filing notices in last 12 months", [ev_id["evidence_id"]] if ev_id else [], [])


def severe_risks(v: SliceView) -> Outcome:
    risks = v.agent_risks()
    if v.raw_findings() is None:
        return unknown("No research findings")
    from .models import Evidence, EvidenceType
    sev = [r for r in risks if r.severity in ("high", "critical")]
    if sev:
        ids = [v.register(Evidence(claim=r.risk, source_url=r.source_url or "about:blank", published_date=r.published_date,
                                   evidence_type=EvidenceType.ANALYST_JUDGMENT, provider="research-agent")) for r in sev]
        return Outcome(Vote.NO, 0.6, f"{len(sev)} high/critical risk(s) identified", [], ids)
    ids = [v.register(Evidence(claim=r.risk, source_url=r.source_url or "about:blank", published_date=r.published_date,
                               evidence_type=EvidenceType.ANALYST_JUDGMENT, provider="research-agent")) for r in risks]
    if not ids:
        return unknown("Research agent reported no risks (absence of evidence is not evidence of absence)")
    return Outcome(Vote.YES, 0.45, f"{len(risks)} risk(s) reviewed, none high/critical", ids, [])


def catalysts_window(lo: int, hi: int, min_n: int, label: str) -> Evaluator:
    def ev(v: SliceView) -> Outcome:
        if v.raw_findings() is None:
            return unknown(f"{label}: no catalyst research")
        from .models import Evidence, EvidenceType
        today = v.as_of.date()
        hits = [c for c in v.catalysts() if c.expected_date and lo <= (c.expected_date - today).days <= hi
                and c.date_confidence in ("confirmed", "estimated")]
        ids = [v.register(Evidence(claim=f"Catalyst: {c.event} ({c.expected_date}, {c.date_confidence})",
                                   source_url=c.source_url or "about:blank", evidence_type=EvidenceType.ANALYST_JUDGMENT,
                                   provider="research-agent")) for c in hits]
        if len(hits) >= min_n:
            return Outcome(Vote.YES, 0.55, f"{label}: {len(hits)} dated catalyst(s)", ids, [])
        return Outcome(Vote.NO, 0.45, f"{label}: {len(hits)} dated catalyst(s) (need {min_n})", [], ids)
    return ev


def material_8k(v: SliceView) -> Outcome:
    filings = v.filings()
    if not filings:
        return unknown("Filing index unavailable")
    hits = [f for f in filings if f["form"] == "8-K" and "1.01" in (f.get("items") or "") and within(f["filed"], v.as_of.date(), 180)]
    idx = v.filing_search("_filings_index")
    if hits:
        return Outcome(Vote.YES, 0.5, f"{len(hits)} 8-K Item 1.01 material agreement(s) in last 180 days", [idx["evidence_id"]] if idx else [], [])
    return Outcome(Vote.NO, 0.35, "No 8-K material definitive agreements in last 180 days", [], [])


def organic(v: SliceView) -> Outcome:
    filings = v.filings()
    if not filings:
        return unknown("Filing index unavailable")
    acq = [f for f in filings if f["form"] == "8-K" and "2.01" in (f.get("items") or "") and within(f["filed"], v.as_of.date(), 450)]
    idx = v.filing_search("_filings_index")
    ids = [idx["evidence_id"]] if idx else []
    if acq:
        return Outcome(Vote.NO, 0.55, f"{len(acq)} completed acquisition(s) (8-K Item 2.01) may inflate reported growth", [], ids)
    return Outcome(Vote.YES, 0.5, "No completed acquisitions (8-K Item 2.01) in last 15 months: growth more likely organic", ids, [])


def persistent_growth(v: SliceView) -> Outcome:
    q = v.revenue_quarters()
    if len(q) < 7:
        return unknown("Fewer than 7 revenue quarters")
    yoy = []
    for i in range(len(q) - 3, len(q)):
        prior = next((p for p in q if 350 <= (q[i].end - p.end).days <= 380), None)
        if prior and prior.value > 0:
            yoy.append(q[i].value / prior.value - 1)
    if len(yoy) < 3:
        return unknown("Cannot compute three consecutive YoY quarters")
    ok = all(g > 0.10 for g in yoy)
    eid = v.fin_ev("revenue_q_yoy")
    return Outcome(Vote.YES if ok else Vote.NO, 0.7, "Last 3 quarters YoY: " + ", ".join(f"{g:.0%}" for g in yoy),
                   [eid] if ok and eid else [], [eid] if not ok and eid else [])


def quality_growth(v: SliceView) -> Outcome:
    gpg, rg = v.fin("gross_profit_growth"), v.fin("revenue_growth_yoy")
    if gpg is None or rg is None:
        return unknown("Gross profit growth unavailable")
    ok = gpg >= 0.8 * rg
    ids = [i for i in (v.fin_ev("gross_profit_growth"), v.fin_ev("revenue_growth_yoy")) if i]
    return Outcome(Vote.YES if ok else Vote.NO, 0.65, f"Gross profit growth {gpg:.1%} vs revenue growth {rg:.1%} (pass-through/commodity test)",
                   ids if ok else [], [] if ok else ids)


def freshness(v: SliceView) -> Outcome:
    if v.raw_findings() is None:
        return unknown("No research findings")
    rows = v.findings()
    dated = [e for e, _ in rows if e.published_date]
    if not dated:
        return unknown("Findings lack publication dates")
    fresh = [e for e in dated if within(e.published_date, v.as_of.date(), 180)]
    ok = len(fresh) >= 0.5 * len(dated)
    return Outcome(Vote.YES if ok else Vote.NO, 0.5, f"{len(fresh)}/{len(dated)} dated findings within 180 days",
                   [v.register(e) for e in fresh] if ok else [], [] if ok else [v.register(e) for e in dated[:3]])


def price_lagging(v: SliceView) -> Outcome:
    md = v.mkt()
    rg = v.fin("revenue_growth_yoy")
    if not md or md.return_12m is None or rg is None:
        return unknown("12-month return or revenue growth unavailable")
    ok = md.return_12m < rg
    ids = [i for i in (v.mkt_ev(), v.fin_ev("revenue_growth_yoy")) if i]
    return Outcome(Vote.YES if ok else Vote.NO, 0.6, f"12m price return {md.return_12m:.0%} vs revenue growth {rg:.0%}",
                   ids if ok else [], [] if ok else ids)


def red_team_balance(v: SliceView) -> Outcome:
    if v.raw_findings() is None:
        return unknown("No research findings")
    rows = v.findings()
    pos, neg = _verified(rows, "positive"), _verified(rows, "negative")
    if not pos and not neg:
        return unknown("No verified findings")
    ok = len(neg) <= len(pos) / 2
    return Outcome(Vote.YES if ok else Vote.NO, 0.5, f"Verified positive {len(pos)} vs negative {len(neg)} (pass if negatives <= half)",
                   [v.register(e) for e in pos] if ok else [], [v.register(e) for e in neg])


def peer_cheap(v: SliceView) -> Outcome:
    val = v.val()
    if not val or val.ev_revenue is None or val.peer_ev_revenue_median is None:
        return unknown("Peer multiple unavailable")
    ok = val.ev_revenue < val.peer_ev_revenue_median
    eid = v.val_ev()
    return Outcome(Vote.YES if ok else Vote.NO, 0.55, f"EV/revenue {val.ev_revenue:.2f}x vs {val.peer_group} peer median {val.peer_ev_revenue_median:.2f}x",
                   [eid] if ok else [], [] if ok else [eid])


def growth_adjusted(v: SliceView) -> Outcome:
    val = v.val()
    if not val or val.ev_revenue is None or not val.revenue_growth_yoy or val.revenue_growth_yoy <= 0:
        return unknown("EV/revenue or positive growth unavailable")
    r = val.ev_revenue / (val.revenue_growth_yoy * 100)
    ok = r <= 0.15
    eid = v.val_ev()
    return Outcome(Vote.YES if ok else Vote.NO, 0.55, f"EV/revenue per point of growth {r:.3f} (test <= 0.15)", [eid] if ok else [], [] if ok else [eid])


def scenario_get(name):
    return lambda val: next((s.upside_pct for s in val.scenarios if s.name == name), None)


def mc_get(attr):
    return lambda val: getattr(val.monte_carlo, attr) if val.monte_carlo else None


def _spec(i, group, dim, q, resp, inputs, fals, fn):
    return (AssignmentSpec(id=i, group=group, dimension=dim, question=q, responsibility=resp, inputs=tuple(inputs), falsification=fals), fn)


def build_registry() -> list[tuple[AssignmentSpec, Evaluator]]:
    US = ("united states", "u.s.", "usa", "us")
    EU = ("eu", "european", "nato", "germany", "france", "poland", "united kingdom", "uk", "nordic", "baltic")
    ASIA = ("japan", "korea", "taiwan", "china", "india")
    OTHER = ("canada", "australia", "brazil", "saudi", "uae", "israel", "mexico", "emerging")
    R = [
        # A. macro & international policy (15)
        _spec(1, "macro_policy", "political", "Is there an enacted US policy with sourced linkage to this company's revenue?", "US federal policy transmission", ["policy"], "Linked US policy is reversed, unfunded, or the company is shown not to qualify", chain_rule("US policy linkage", lambda c: _country_in(US)(c) and c.stage in ACTIVE_STAGES)),
        _spec(2, "macro_policy", "political", "Is there an EU/NATO-Europe policy with sourced linkage to company revenue?", "European policy transmission", ["policy"], "European programme awards go to competitors or budgets are cut", chain_rule("EU/NATO policy linkage", _country_in(EU))),
        _spec(3, "macro_policy", "political", "Is there an Asian (JP/KR/TW/CN/IN) policy with sourced linkage to company revenue?", "Asian policy transmission", ["policy"], "Asian policy excludes foreign suppliers or is withdrawn", chain_rule("Asia policy linkage", _country_in(ASIA))),
        _spec(4, "macro_policy", "political", "Is there a Canada/Australia/emerging-market policy with sourced linkage to company revenue?", "Other-region policy transmission", ["policy"], "Programme cancelled or awarded elsewhere", chain_rule("Other-region policy linkage", _country_in(OTHER))),
        _spec(5, "macro_policy", "political", "Do active policy tailwinds outnumber active headwinds for the company's industries?", "Net policy direction for tagged industries", ["policy"], "New tariffs/export controls on the company's inputs or markets take effect", headwind_absent),
        _spec(6, "macro_policy", "political", "Has a linked policy moved beyond proposal into implementation or enforcement?", "Policy lifecycle stage", ["policy"], "Linked policy stalls at proposal stage through the next budget cycle", chain_rule("Implementation-stage linkage", lambda c: c.stage in ("implementation", "enforcement"))),
        _spec(7, "macro_policy", "political", "Are linked policies durable through the 12-month thesis window (not expiring/reversed)?", "Policy durability & reversal risk", ["policy"], "Election, court ruling or sunset clause removes the linked policy", policy_durable),
        _spec(8, "macro_policy", "political", "Is there verified company-level evidence of political/industrial-policy benefit?", "Company political-dimension evidence", ["findings"], "Company disclosures show no policy-driven orders", f_pos("Political evidence", {"political"})),
        _spec(9, "macro_policy", "economic", "Is there verified evidence of favorable economic demand drivers for the company?", "Company economic-dimension evidence", ["findings"], "Demand indicators (orders, guidance) roll over", f_pos("Economic evidence", {"economic"})),
        _spec(10, "macro_policy", "economic", "Is the balance sheet insulated from higher-for-longer interest rates?", "Interest-rate sensitivity", ["financials"], "Net debt/EBITDA rises above 3x or refinancing at materially higher rates", rate_sensitivity),
        _spec(11, "macro_policy", "economic", "Does the company have evidenced non-US policy-linked revenue (international diversification)?", "International revenue exposure", ["policy"], "International revenue share falls or programmes exclude the company", chain_rule("Non-US revenue linkage", lambda c: not _country_in(US)(c))),
        _spec(12, "macro_policy", "environmental", "Is there verified evidence that energy/grid/mineral/climate investment drives company demand?", "Environmental-dimension demand", ["findings"], "Utility/energy capex guidance cut in company's end markets", f_pos("Environmental evidence", {"environmental"})),
        _spec(13, "macro_policy", "social", "Is there verified evidence of social/adoption shifts supporting demand?", "Social-dimension demand", ["findings"], "Adoption metrics stall or reverse", f_pos("Social evidence", {"social"})),
        _spec(14, "macro_policy", "political", "Does at least one policy chain carry direct evidence of company revenue (not inference)?", "Policy-to-revenue evidence test", ["policy"], "Cited revenue evidence is retracted or shown unrelated to the policy", chain_rule("Revenue-evidenced chain", lambda c: True)),
        _spec(15, "macro_policy", "political", "Are evidenced policy linkages diversified across at least two countries?", "Policy concentration risk", ["policy"], "All linked policy exposure collapses to one government", lambda v: (lambda cs: unknown("No company linkages") if not cs else Outcome(Vote.YES if len({c.country for c in cs}) >= 2 else Vote.NO, 0.5, f"{len({c.country for c in cs})} countries in evidenced linkages", sorted({i for c in cs for i in c.evidence_ids}) if len({c.country for c in cs}) >= 2 else [], [] if len({c.country for c in cs}) >= 2 else sorted({i for c in cs for i in c.evidence_ids})[:2]))([c for c in v.chains() if c.company == v.ticker and c.evidence_of_company_revenue])),
        # B. company financial (15)
        _spec(16, "company_financial", "economic", "Is TTM revenue growth at least 20% YoY?", "Trailing revenue growth", ["financials"], "Next 10-Q shows TTM growth below 20%", m_thresh("revenue_growth_yoy", ">=", 0.20, "TTM revenue growth")),
        _spec(17, "company_financial", "economic", "Is latest-quarter revenue growth at least 20% YoY?", "Current-quarter growth", ["financials"], "Next quarter YoY growth below 20%", m_thresh("revenue_q_yoy", ">=", 0.20, "Latest-quarter growth")),
        _spec(18, "company_financial", "economic", "Is quarterly YoY revenue growth accelerating?", "Growth acceleration", ["financials"], "Growth decelerates in the next reported quarter", m_thresh("revenue_acceleration", ">", 0.0, "Growth acceleration")),
        _spec(19, "company_financial", "economic", "Is TTM gross margin at least 30%?", "Gross margin level", ["financials"], "Gross margin falls below 30%", m_thresh("gross_margin", ">=", 0.30, "Gross margin")),
        _spec(20, "company_financial", "economic", "Is gross margin expanding YoY?", "Gross margin trend", ["financials"], "Gross margin contracts YoY", m_thresh("gross_margin_change", ">", 0.0, "Gross margin change")),
        _spec(21, "company_financial", "economic", "Is TTM operating margin positive?", "Operating profitability", ["financials"], "Operating loss in TTM", m_thresh("operating_margin", ">", 0.0, "Operating margin")),
        _spec(22, "company_financial", "economic", "Is operating margin expanding YoY (operating leverage)?", "Operating leverage", ["financials"], "Operating margin contracts YoY", m_thresh("operating_margin_change", ">", 0.0, "Operating margin change")),
        _spec(23, "company_financial", "economic", "Is TTM free cash flow positive?", "Free cash flow level", ["financials"], "TTM FCF turns negative", m_thresh("fcf_ttm", ">", 0.0, "TTM FCF", pct=False)),
        _spec(24, "company_financial", "economic", "Is TTM free cash flow improving YoY?", "Free cash flow trend", ["financials"], "TTM FCF declines YoY", m_thresh("fcf_change", ">", 0.0, "FCF change", pct=False)),
        _spec(25, "company_financial", "economic", "Is funding runway adequate (FCF positive or >=24 months)?", "Liquidity runway", ["financials"], "Runway falls below 24 months", runway_ok),
        _spec(26, "company_financial", "economic", "Does the company hold net cash?", "Net cash position", ["financials"], "Debt exceeds cash", net_cash),
        _spec(27, "company_financial", "legal", "Is share-count dilution at most 5% YoY?", "Dilution discipline", ["financials"], "Share count rises >5% over 12 months", m_thresh("dilution_yoy", "<=", 0.05, "Share-count change")),
        _spec(28, "company_financial", "economic", "Is stock-based compensation at most 10% of revenue?", "SBC burden", ["financials"], "SBC exceeds 10% of revenue", sbc_ratio),
        _spec(29, "company_financial", "economic", "Is backlog (RPO) growing at least 10% YoY?", "Backlog growth (leading indicator)", ["financials"], "RPO flat or declining YoY", m_thresh("backlog_growth_yoy", ">=", 0.10, "Backlog growth")),
        _spec(30, "company_financial", "economic", "Is backlog at least 1x latest-quarter revenue (book-to-bill proxy)?", "Backlog coverage", ["financials"], "Backlog coverage falls below 1x quarterly revenue", m_thresh("backlog_to_quarterly_revenue", ">=", 1.0, "Backlog / quarterly revenue", pct=False)),
        # C. technology & competitive (15)
        _spec(31, "technology_competitive", "technological", "Is there verified evidence of a technological advantage?", "Technology moat evidence", ["findings"], "Competitor matches the capability or customers dual-source", f_pos("Technology evidence", {"technological"})),
        _spec(32, "technology_competitive", "technological", "Is there verified evidence of new product launches or qualifications?", "Product pipeline", ["findings"], "Product delays or failed qualification", f_pos("Product evidence", None, {"product"})),
        _spec(33, "technology_competitive", "technological", "Is the company free of verified adverse competitive developments?", "Competitive threat scan", ["findings"], "Verified share loss or price war", f_no_neg("Competition", None, {"competition"})),
        _spec(34, "technology_competitive", "technological", "Is there verified evidence of manufacturing capacity expansion?", "Capacity expansion", ["findings"], "Capacity projects delayed or cancelled", f_pos("Capacity evidence", None, {"capacity"})),
        _spec(35, "technology_competitive", "social", "Is there verified evidence of new customer wins?", "Customer adoption", ["findings"], "Key customer churn", f_pos("Customer wins", None, {"customer", "contract"})),
        _spec(36, "technology_competitive", "economic", "Is the company free of verified customer-concentration or customer-loss problems?", "Customer risk scan", ["findings"], "A top customer reduces orders", f_no_neg("Customer risk", None, {"customer"})),
        _spec(37, "technology_competitive", "technological", "Is gross margin at least 40% (pricing-power proxy)?", "Pricing power", ["financials"], "Gross margin below 40%", m_thresh("gross_margin", ">=", 0.40, "Gross margin (moat proxy)")),
        _spec(38, "technology_competitive", "technological", "Is R&D intensity between 3% and 35% of revenue?", "Innovation investment", ["financials"], "R&D cut below 3% or burn above 35%", rd_intensity),
        _spec(39, "technology_competitive", "legal", "Is there verified patent/IP evidence supporting the moat?", "Intellectual property", ["findings"], "Patent invalidated or design-around", f_pos("IP evidence", None, None, ("patent", "intellectual property", "proprietary"))),
        _spec(40, "technology_competitive", "technological", "Does sourced evidence tie a supply-chain bottleneck to company revenue?", "Bottleneck position", ["policy"], "Bottleneck resolved by new capacity elsewhere", bottleneck),
        _spec(41, "technology_competitive", "technological", "Is there verified adoption evidence in AI/data-center/defense/electrification end markets?", "Adoption-curve exposure", ["findings"], "End-market adoption slows", f_pos("Adoption evidence", None, None, ("ai", "data center", "drone", "defense", "grid", "battery", "electrif"))),
        _spec(42, "technology_competitive", "technological", "Is the company free of verified technology disruption or obsolescence risk?", "Disruption scan", ["findings"], "Substitute technology wins designs", f_no_neg("Technology risk", {"technological"})),
        _spec(43, "technology_competitive", "economic", "Is revenue per employee at least $250k?", "Operating efficiency", ["financials", "market"], "Revenue per employee falls below $250k", rev_per_employee),
        _spec(44, "technology_competitive", "technological", "Is there verified capacity/backlog evidence published within 180 days?", "Recency of scale evidence", ["findings"], "No new capacity/backlog disclosures", f_pos("Recent scale evidence", None, {"capacity", "backlog"}, (), 1, 180)),
        _spec(45, "technology_competitive", "technological", "Are technology claims corroborated by at least two independent source domains?", "Source independence", ["findings"], "Corroborating source retracts", multi_source),
        # D. valuation & mispricing (15)
        _spec(46, "valuation_mispricing", "economic", "Does the bull-case implied price reach at least +100%?", "Doubling test", ["valuation"], "Bull-case inputs revised so implied price < 2x", val_rule("Bull-case upside", scenario_get("bull"), ">=", 1.0)),
        _spec(47, "valuation_mispricing", "economic", "Is base-case implied upside at least 30%?", "Base-case attractiveness", ["valuation"], "Base case upside below 30%", val_rule("Base-case upside", scenario_get("base"), ">=", 0.30)),
        _spec(48, "valuation_mispricing", "economic", "Is bear-case downside no worse than -50%?", "Downside bound", ["valuation"], "Bear case implies > 50% loss", val_rule("Bear-case return", scenario_get("bear"), ">=", -0.50)),
        _spec(49, "valuation_mispricing", "economic", "Is revenue growth required to double (at current multiple) at most 60%?", "Plausibility of doubling math", ["valuation"], "Required growth exceeds 60%", val_rule("Growth required to double", lambda val: val.growth_required_to_double_at_current_multiple, "<=", 0.60)),
        _spec(50, "valuation_mispricing", "economic", "Is EV/revenue below the sector peer median?", "Relative valuation", ["valuation"], "Multiple exceeds peer median", peer_cheap),
        _spec(51, "valuation_mispricing", "economic", "Is EV/revenue per point of growth at most 0.15?", "Growth-adjusted valuation", ["valuation"], "Growth-adjusted multiple above 0.15", growth_adjusted),
        _spec(52, "valuation_mispricing", "economic", "Is P/E at most 30 (when profitable)?", "Earnings valuation", ["valuation"], "P/E above 30", val_rule("P/E", lambda val: val.pe, "<=", 30, "{:.1f}")),
        _spec(53, "valuation_mispricing", "economic", "Is EV/EBITDA at most 20 (when EBITDA positive)?", "Cash-earnings valuation", ["valuation"], "EV/EBITDA above 20", val_rule("EV/EBITDA", lambda val: val.ev_ebitda, "<=", 20, "{:.1f}")),
        _spec(54, "valuation_mispricing", "economic", "Is Monte Carlo model-implied P(price >= 2x) at least 20%?", "Simulated upside", ["valuation"], "Re-run with updated inputs drops below 20%", val_rule("MC P(double)", mc_get("p_double"), ">=", 0.20)),
        _spec(55, "valuation_mispricing", "economic", "Is Monte Carlo model-implied P(price <= 0.5x) at most 20%?", "Simulated downside", ["valuation"], "Re-run exceeds 20%", val_rule("MC P(-50%)", mc_get("p_loss_50"), "<=", 0.20)),
        _spec(56, "valuation_mispricing", "economic", "Has the stock risen less than 100% over 12 months (opportunity not already captured)?", "Prior move check", ["market"], "Stock doubles before thesis milestones", mkt_rule("12m return", lambda m: m.return_12m, "<", 1.0, "{:.0%}")),
        _spec(57, "valuation_mispricing", "economic", "Is the price at least 30% below its 52-week high?", "Distance from prior highs", ["market"], "Price within 30% of 52w high", mkt_rule("Below 52w high", lambda m: (1 - m.price / m.high_52w) if m.price and m.high_52w else None, ">=", 0.30, "{:.0%}")),
        _spec(58, "valuation_mispricing", "economic", "Is market capitalization at most $5B (small/mid, less-covered)?", "Size / coverage proxy", ["market"], "Market cap exceeds $5B", mkt_rule("Market cap", lambda m: m.market_cap, "<=", 5e9, "${:,.0f}")),
        _spec(59, "valuation_mispricing", "social", "Is average daily turnover at most 1% of float (low attention)?", "Attention proxy (turnover)", ["market"], "Turnover spikes above 1% of float persistently", mkt_rule("Daily turnover", lambda m: m.turnover_daily, "<=", 0.01, "{:.2%}")),
        _spec(60, "valuation_mispricing", "economic", "Is revenue required to double at the peer multiple at most 1.6x TTM revenue?", "Peer-multiple doubling math", ["valuation"], "Requirement exceeds 1.6x", val_rule("Revenue needed at peer multiple / TTM", lambda val: (val.revenue_required_to_double_at_peer_multiple / val.revenue_ttm) if val.revenue_required_to_double_at_peer_multiple and val.revenue_ttm else None, "<=", 1.6, "{:.2f}x")),
        # E. military & geopolitical (10)
        _spec(61, "military_geopolitical", "military", "Is there verified evidence of military demand for company products?", "Military demand", ["findings"], "Programme cancelled or company loses down-select", f_pos("Military evidence", {"military"})),
        _spec(62, "military_geopolitical", "military", "Has the company received name-matched US federal contract awards in the last 12 months?", "Federal award presence", ["contracts"], "Awards are shown to belong to a different recipient", awards_any),
        _spec(63, "military_geopolitical", "military", "Are federal awards at least 5% of TTM revenue?", "Federal award materiality", ["contracts", "financials"], "Award value falls below 5% of revenue", awards_material),
        _spec(64, "military_geopolitical", "military", "Is there an implemented defense policy linkage (drones, counter-UAS, shipbuilding, munitions, sonar)?", "Defense policy transmission", ["policy"], "Defense budget line items cut", chain_rule("Defense linkage", lambda c: any(t in (c.industry + c.policy).lower() for t in DEFENSE_TAGS) and c.stage in ACTIVE_STAGES)),
        _spec(65, "military_geopolitical", "military", "Is there an evidenced NATO/European defense linkage?", "NATO/EU defense exposure", ["policy"], "European procurement favors domestic suppliers", chain_rule("NATO/EU defense", lambda c: _country_in(EU)(c) and any(t in (c.industry + c.policy).lower() for t in DEFENSE_TAGS))),
        _spec(66, "military_geopolitical", "military", "Is there an evidenced Indo-Pacific defense linkage?", "Indo-Pacific defense exposure", ["policy"], "Regional programmes exclude the company", chain_rule("Indo-Pacific defense", lambda c: _country_in(("japan", "korea", "taiwan", "australia", "india"))(c))),
        _spec(67, "military_geopolitical", "military", "Is the company free of verified adverse military/geopolitical developments?", "Geopolitical risk scan", ["findings"], "Lost programme or sanctions exposure", f_no_neg("Military/geopolitical risk", {"military"})),
        _spec(68, "military_geopolitical", "military", "Is demand dual-use (verified military and commercial)?", "Dual-use resilience", ["findings"], "One market disappears", dual_use),
        _spec(69, "military_geopolitical", "political", "Is the company free of verified China/export-control/tariff headwinds?", "China dependence scan", ["findings"], "New export controls or tariffs hit inputs/customers", china_exposure),
        _spec(70, "military_geopolitical", "military", "Is there contract-award evidence within the last 120 days?", "Award recency", ["contracts", "findings"], "No new awards for two quarters", award_recent),
        # F. supply chain & industrial policy (10)
        _spec(71, "supply_chain_industrial", "political", "Is there an evidenced reshoring/tariff/industrial-policy tailwind tied to company revenue?", "Reshoring transmission", ["policy"], "Tariff relief removes the domestic-supplier advantage", chain_rule("Reshoring/tariff linkage", lambda c: any(k in (c.policy + c.revenue_mechanism).lower() for k in ("tariff", "reshor", "domestic", "buy american", "chips", "ira", "232", "301", "onshor")))),
        _spec(72, "supply_chain_industrial", "economic", "Is there verified evidence the company supplies large-capex customers (primes, hyperscalers, utilities)?", "Small supplier to large capex", ["findings"], "Large customer insources or switches", f_pos("Supplier-to-capex evidence", None, {"customer", "contract"}, ("prime", "hyperscal", "utility", "utilities", "lockheed", "northrop", "raytheon", "rtx", "general dynamics", "boeing", "army", "navy", "air force", "department of"))),
        _spec(73, "supply_chain_industrial", "economic", "Is inventory growth disciplined relative to revenue growth?", "Inventory discipline", ["financials"], "Inventory grows >10 pts faster than revenue", inventory_discipline),
        _spec(74, "supply_chain_industrial", "economic", "Is capex rising (capacity investment ahead of demand)?", "Capacity investment", ["financials"], "Capex cut", capex_rising),
        _spec(75, "supply_chain_industrial", "environmental", "Is there an evidenced energy/grid/critical-mineral policy linkage?", "Energy & minerals transmission", ["policy"], "Grid/mineral programmes defunded", chain_rule("Energy/mineral linkage", lambda c: any(k in (c.industry + c.policy).lower() for k in ("grid", "transmission", "energy", "storage", "battery", "mineral", "data_center", "data center", "power", "utilit")))),
        _spec(76, "supply_chain_industrial", "economic", "Is the company free of verified supply shortages or supplier problems?", "Supply risk scan", ["findings"], "Input shortage or supplier failure", f_no_neg("Supply risk", None, None, ("supply", "shortage", "supplier", "input", "component"))),
        _spec(77, "supply_chain_industrial", "political", "Is any linked policy at enforcement or implementation stage with revenue evidence?", "Enforcement-stage evidence", ["policy"], "Enforcement delayed", chain_rule("Enforcement-stage revenue linkage", lambda c: c.stage in ("enforcement", "implementation"))),
        _spec(78, "supply_chain_industrial", "political", "Is there verified evidence of grants, subsidies, loans or awards to the company?", "Subsidy capture", ["findings"], "Grant rescinded", f_pos("Subsidy evidence", None, None, ("grant", "subsid", "loan", "tax credit", "45x", "award"))),
        _spec(79, "supply_chain_industrial", "economic", "Is the customer base diversified (>=2 verified wins, no concentration flag)?", "Customer diversification", ["findings"], "Concentration disclosed", diversified_customers),
        _spec(80, "supply_chain_industrial", "economic", "Does operating cash flow convert at least half of EBITDA?", "Cash conversion", ["financials"], "Working capital absorbs cash", cash_conversion),
        # G. risk, accounting & forensic (10)
        _spec(81, "risk_forensic", "legal", "Are filings free of going-concern doubt over the last 12 months?", "Going concern", ["risks", "filings"], "Auditor adds going-concern paragraph", going_concern),
        _spec(82, "risk_forensic", "legal", "Are filings free of 'material weakness' disclosures over the last 12 months?", "Internal controls", ["filings"], "Material weakness disclosed", fts_absent("material weakness", "Material weakness")),
        _spec(83, "risk_forensic", "legal", "Are filings free of non-reliance/restatement notices over the last 12 months?", "Restatement risk", ["filings"], "Item 4.02 non-reliance filed", fts_absent("non-reliance", "Non-reliance/restatement")),
        _spec(84, "risk_forensic", "economic", "Is operating cash flow at least net income (accrual quality)?", "Accruals quality", ["financials"], "Earnings outpace cash flow", accruals),
        _spec(85, "risk_forensic", "legal", "Is the company free of dilutive financings in the last 12 months?", "Dilution events", ["risks", "financials", "findings"], "New offering/ATM/convert", dilution_events),
        _spec(86, "risk_forensic", "economic", "Is leverage at most 3x EBITDA (or net cash)?", "Leverage", ["financials"], "Leverage exceeds 3x", leverage),
        _spec(87, "risk_forensic", "economic", "Is stockholders' equity positive?", "Solvency", ["financials"], "Equity turns negative", m_thresh("stockholders_equity", ">", 0.0, "Stockholders' equity", pct=False)),
        _spec(88, "risk_forensic", "legal", "Is the listing compliant and price above $1?", "Exchange listing", ["market"], "Deficiency notice or price below $1", listing_ok),
        _spec(89, "risk_forensic", "legal", "Is the company free of late-filing notices (NT 10-K/10-Q) in 12 months?", "Filing timeliness", ["filings"], "NT filing", late_filings),
        _spec(90, "risk_forensic", "legal", "Is the company free of high/critical risks identified by research?", "Research risk register", ["risks", "findings"], "A high/critical risk materializes", severe_risks),
        # H. catalyst timing & alternative hypotheses (10)
        _spec(91, "catalyst_alternative", "economic", "Is there a dated catalyst 3-12 months out?", "Catalyst timing (3-12m)", ["catalysts", "findings"], "Catalyst slips beyond 12 months", catalysts_window(90, 365, 1, "Catalysts 3-12m")),
        _spec(92, "catalyst_alternative", "economic", "Is there a dated catalyst within 90 days?", "Near-term catalyst", ["catalysts", "findings"], "No event in 90 days", catalysts_window(0, 90, 1, "Catalysts 0-90d")),
        _spec(93, "catalyst_alternative", "economic", "Are there at least two distinct dated catalysts within 12 months?", "Catalyst breadth", ["catalysts", "findings"], "Only one catalyst remains", catalysts_window(0, 365, 2, "Catalysts 0-12m")),
        _spec(94, "catalyst_alternative", "legal", "Has the company filed an 8-K material definitive agreement in 180 days?", "Contract momentum (SEC)", ["filings"], "No new material agreements", material_8k),
        _spec(95, "catalyst_alternative", "economic", "Alternative hypothesis: is growth organic (no completed acquisition in 15 months)?", "Acquisition-inflated growth check", ["filings"], "Acquisition disclosed", organic),
        _spec(96, "catalyst_alternative", "economic", "Alternative hypothesis: has growth persisted >10% YoY for 3 consecutive quarters?", "One-off growth check", ["financials"], "Any of the next quarters below 10%", persistent_growth),
        _spec(97, "catalyst_alternative", "economic", "Alternative hypothesis: is gross profit growing with revenue (not pass-through/commodity)?", "Revenue quality check", ["financials"], "Gross profit lags revenue", quality_growth),
        _spec(98, "catalyst_alternative", "social", "Is the evidence base fresh (>=50% of dated findings within 180 days)?", "Evidence staleness", ["findings"], "No new findings for 6 months", freshness),
        _spec(99, "catalyst_alternative", "economic", "Has the share price lagged revenue growth over 12 months (not yet priced)?", "Priced-in check", ["market", "financials"], "Price outruns fundamentals", price_lagging),
        _spec(100, "catalyst_alternative", "social", "Red-team: are verified negatives at most half the verified positives?", "Adversarial balance", ["findings"], "New verified negatives accumulate", red_team_balance),
    ]
    assert len(R) == 100 and len({s.id for s, _ in R}) == 100
    counts: dict[str, int] = {}
    for s, _ in R:
        counts[s.group] = counts.get(s.group, 0) + 1
    assert counts == GROUPS, counts
    return R


REGISTRY = build_registry()
