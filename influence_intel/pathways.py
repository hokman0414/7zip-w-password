"""Influence pathways: the channels through which an organization sustains standing and influence, each assessed with
explicit evidence-backed checks. A check with no data is UNKNOWN and is excluded from the strength score, never a pass."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from .collect import Dataset, lda_quarters, latest_qkey
from .models import Check, Direction, Evidence, EvidenceType, PathwayAssessment


@dataclass(frozen=True)
class Pathway:
    id: str
    label: str
    dimension: str
    levers: tuple[str, ...]


# Levers are lawful, transparent options an analyst would test against the evidence. They are analyst judgment, not
# findings, and exclude deception, coercion, covert foreign influence or anything that violates campaign-finance or
# tax-exemption rules.
PATHWAYS = [
    Pathway("membership_base", "Membership and adherent base", "social", (
        "Young-adult, family and multilingual programs where affiliation data show growth",
        "Track affiliation surveys (Pew, PRRI, ARDA) and attendance as leading signposts")),
    Pathway("institutional_trust", "Institutional trust and governance", "social", (
        "Independent safeguarding audits and public accountability reporting",
        "Financial transparency beyond legal minimums to rebuild donor and public trust")),
    Pathway("institutional_services", "Schools, health and social-service institutions", "social", (
        "Service partnerships (health, education, refugee, food) that create durable public reliance",
        "Workforce and compliance capacity to keep public-funding eligibility")),
    Pathway("financial_resources", "Financial resources", "economic", (
        "Diversify revenue: planned giving, endowment, donor-advised funds, online giving",
        "Reserve policy sized to legal, demographic and policy shocks")),
    Pathway("federal_partnerships", "Government grants and contracts", "economic", (
        "Compete for program grants aligned with service mission; track rule changes on faith-based eligibility",
        "Diversify funders so a single agency or program cut is survivable")),
    Pathway("legislative_lobbying", "Legislative and executive advocacy", "political", (
        "Register affiliates in-house for continuity and named-bill tracking",
        "Shift effort to state legislatures and agency rulemaking when federal action stalls")),
    Pathway("electoral_engagement", "Electoral engagement (within legal limits)", "political", (
        "Nonpartisan voter education by 501(c)(3)s; partisan activity only through separately funded, registered entities",
        "Candidate questionnaires and issue scorecards published transparently")),
    Pathway("coalitions_alliances", "Coalitions and alliances", "political", (
        "Interfaith and cross-ideological coalitions on shared issues widen legitimacy",
        "Sign-on letters and joint amicus briefs to multiply voice without new spend")),
    Pathway("legal_advocacy", "Legal advocacy and litigation", "legal", (
        "Strategic litigation and amicus participation on religious-liberty and conscience cases",
        "Compliance programs that pre-empt adverse rulings and settlements")),
    Pathway("media_public_salience", "Media and public salience", "social", (
        "Earned media built on service work rather than conflict coverage",
        "Rapid, transparent response protocol for crises")),
    Pathway("digital_reach", "Digital and technological reach", "technological", (
        "Streaming, podcasts and social channels; measured with audience data, not follower counts",
        "Data-protection and AI-use policies for congregant data")),
    Pathway("transnational_network", "Transnational network and diplomacy", "military", (
        "Diaspora and partner-church networks; humanitarian partnerships in conflict regions",
        "Monitor security and sanctions regimes affecting cross-border activity")),
    Pathway("land_and_property", "Land, property and environmental stewardship", "environmental", (
        "Mission-aligned property use: housing, schools, conservation easements",
        "Climate and stewardship commitments that align with younger members")),
]
BY_ID = {p.id: p for p in PATHWAYS}


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def independent(evs: list[Evidence]) -> int:
    """Distinct source domains: ten articles quoting one press release count once per outlet, not ten times."""
    return len({_domain(e.source_url) for e in evs})


def _research_checks(ds: Dataset, pid: str) -> list[Check]:
    evs = [e for e in ds.by_pathway(pid) if e.provider == "research-agent"]
    if ds.research is None:
        return [Check(id=f"{pid}:research", question="Researched evidence on this pathway?", result=None,
                      detail="no research file; run research subagents")]
    pos = [e for e in evs if e.direction == Direction.STRENGTHENS]
    neg = [e for e in evs if e.direction == Direction.WEAKENS]
    vpos = [e for e in pos if e.evidence_type == EvidenceType.VERIFIED]
    vneg = [e for e in neg if e.evidence_type == EvidenceType.VERIFIED]
    out = [Check(id=f"{pid}:verified_support", question="At least one verified finding strengthens this pathway?",
                 result=bool(vpos) if evs else None, evidence_ids=[e.id for e in vpos]),
           Check(id=f"{pid}:no_verified_damage", question="No verified finding weakens this pathway?",
                 result=(not vneg) if evs else None, evidence_ids=[e.id for e in vneg])]
    if pos or neg:
        out.append(Check(id=f"{pid}:balance", question="Strengthening evidence from more independent sources than weakening?",
                         result=independent(pos) > independent(neg),
                         detail=f"{independent(pos)} vs {independent(neg)} independent source domains",
                         evidence_ids=[e.id for e in pos + neg]))
    return out


def _lobbying(ds: Dataset) -> tuple[list[Check], str]:
    configured = any(a.lda_client_names or a.lda_registrant_names for a in ds.profile.affiliates)
    q = lda_quarters(ds)
    L = latest_qkey(ds)
    last4, prior4 = range(L - 3, L + 1), range(L - 7, L - 3)
    rows4 = [r for k in last4 for r in q.get(k, [])]
    rowsp = [r for k in prior4 for r in q.get(k, [])]
    ids4 = [r["evidence_id"] for r in rows4]
    active8 = sum(1 for k in range(L - 7, L + 1) if q.get(k))
    s4 = sum(r["amount"] or 0 for r in rows4)
    sp = sum(r["amount"] or 0 for r in rowsp)
    issues4 = {c for r in rows4 for c in r["issue_codes"]}
    gov4 = {g for r in rows4 for a in r["activities"] for g in a["government_entities"]}
    bills4 = {b for r in rows4 for b in r["bills"]}
    unk = None if not configured else False
    checks = [
        Check(id="lobby:continuity", question="Lobbying disclosed in at least 6 of the last 8 quarters?",
              result=(active8 >= 6) if configured else None, detail=f"{active8}/8 quarters", evidence_ids=ids4),
        Check(id="lobby:spend_trend", question="Disclosed spend in the last 4 quarters at or above the prior 4?",
              result=(s4 >= sp) if (s4 and sp) else None, detail=f"${s4:,.0f} vs ${sp:,.0f}", evidence_ids=ids4),
        Check(id="lobby:breadth", question="Lobbies on 3 or more issue areas in the last 4 quarters?",
              result=(len(issues4) >= 3) if rows4 else unk, detail=", ".join(sorted(issues4)), evidence_ids=ids4),
        Check(id="lobby:reach", question="Contacts 3 or more government entities (chambers, agencies)?",
              result=(len(gov4) >= 3) if rows4 else unk, detail=", ".join(sorted(gov4)[:8]), evidence_ids=ids4),
        Check(id="lobby:named_bills", question="Names specific bills in the last 4 quarters?",
              result=bool(bills4) if rows4 else unk, detail=", ".join(sorted(bills4)[:10]), evidence_ids=ids4),
    ]
    checks += [c for c in _research_checks(ds, "legislative_lobbying") if not c.id.endswith(":research")]
    n4, np_ = len(rows4), len(rowsp)
    if s4 and sp:
        trend = "rising" if s4 > 1.1 * sp else "declining" if s4 < 0.9 * sp else "stable"
    elif n4 or np_:
        trend = "rising" if n4 > np_ else "declining" if n4 < np_ else "stable"
    else:
        trend = "unknown"
    return checks, trend


def _finance(ds: Dataset) -> tuple[list[Check], str]:
    pairs = [(rows[-1], rows[-2]) for rows in ds.nonprofit.values() if len(rows) >= 2]
    latest = [rows[-1] for rows in ds.nonprofit.values() if rows]
    if not latest:
        return [Check(id="fin:data", question="Form 990 financials available for any affiliate?", result=None,
                      detail="no EIN configured or no public 990 (churches are not required to file)"),
                *_research_checks(ds, "financial_resources")], "unknown"
    ids = [r["evidence_id"] for p in pairs for r in p] or [r["evidence_id"] for r in latest]
    rev_now = sum(a["revenue"] or 0 for a, _ in pairs)
    rev_prev = sum(b["revenue"] or 0 for _, b in pairs)
    ast_now = sum(a["assets"] or 0 for a, _ in pairs)
    ast_prev = sum(b["assets"] or 0 for _, b in pairs)
    rev_l = sum(r["revenue"] or 0 for r in latest)
    exp_l = sum(r["expenses"] or 0 for r in latest)
    con_l = sum(r["contributions"] or 0 for r in latest)
    checks = [
        Check(id="fin:revenue_growth", question="Combined affiliate revenue grew in the latest filed year?",
              result=(rev_now > rev_prev) if pairs and rev_prev else None, detail=f"${rev_now:,.0f} vs ${rev_prev:,.0f}", evidence_ids=ids),
        Check(id="fin:asset_growth", question="Combined total assets grew in the latest filed year?",
              result=(ast_now > ast_prev) if pairs and ast_prev else None, detail=f"${ast_now:,.0f} vs ${ast_prev:,.0f}", evidence_ids=ids),
        Check(id="fin:surplus", question="Latest revenue covers expenses (no operating deficit)?",
              result=(rev_l >= exp_l) if rev_l else None, detail=f"${rev_l:,.0f} vs ${exp_l:,.0f}", evidence_ids=ids),
        Check(id="fin:donor_base", question="Contributions are at least 25% of revenue (broad donor support)?",
              result=(con_l / rev_l >= 0.25) if rev_l else None, detail=f"{(con_l / rev_l if rev_l else 0):.0%}", evidence_ids=ids),
    ]
    trend = "unknown" if not pairs or not rev_prev else "rising" if rev_now > 1.05 * rev_prev else "declining" if rev_now < 0.95 * rev_prev else "stable"
    return checks, trend


def _services(ds: Dataset) -> tuple[list[Check], str]:
    big = [rows[-1] for name, rows in ds.nonprofit.items() if rows and (rows[-1]["expenses"] or 0) >= 10e6
           and next((a.relation for a in ds.profile.affiliates if a.name == name), "") not in ("core", "pac", "advocacy")]
    cfg_awards = any(a.usaspending_names for a in ds.profile.affiliates)
    checks = [Check(id="svc:scale", question="Operates a service institution with $10M+ annual expenses?",
                    result=bool(big) if ds.nonprofit else None, evidence_ids=[r["evidence_id"] for r in big],
                    detail=", ".join(r["name"] or "" for r in big)),
              Check(id="svc:public_funding", question="Receives federal grants or contracts for services?",
                    result=bool(ds.awards) if cfg_awards else None, evidence_ids=[r["evidence_id"] for r in ds.awards[:10]])]
    return checks + _research_checks(ds, "institutional_services"), "unknown"


def _federal(ds: Dataset) -> tuple[list[Check], str]:
    if not any(a.usaspending_names for a in ds.profile.affiliates):
        return [Check(id="fed:data", question="USAspending recipient names configured?", result=None)], "unknown"
    ids = [r["evidence_id"] for r in ds.awards]
    agencies = {r["agency"] for r in ds.awards if r["agency"]}
    grants = sum(r["amount"] for r in ds.awards if r["kind"] == "grant")
    yrs = defaultdict(float)
    for r in ds.awards:
        if r["start_date"]:
            yrs[r["start_date"].year] += r["amount"]
    y = ds.as_of.year
    trend = "unknown"
    if yrs.get(y - 1) or yrs.get(y - 2):
        a, b = yrs.get(y - 1, 0) + yrs.get(y, 0), yrs.get(y - 2, 0)
        trend = "rising" if a > 1.1 * b else "declining" if a < 0.9 * b else "stable"
    return [Check(id="fed:any", question="Federal awards in the last 3 years?", result=bool(ds.awards), evidence_ids=ids[:10]),
            Check(id="fed:agencies", question="Awards from 2 or more agencies?", result=len(agencies) >= 2,
                  detail=", ".join(sorted(agencies)[:6]), evidence_ids=ids[:10]),
            Check(id="fed:scale", question="Grant total at least $1M?", result=grants >= 1e6, detail=f"${grants:,.0f}", evidence_ids=ids[:10]),
            *_research_checks(ds, "federal_partnerships")], trend


def _electoral(ds: Dataset) -> tuple[list[Check], str]:
    if not any(a.fec_committee_ids for a in ds.profile.affiliates):
        return [Check(id="fec:data", question="Affiliated FEC committee configured?", result=None,
                      detail="501(c)(3) religious bodies may not campaign; only separately registered committees appear")], "unknown"
    cycles = sorted({r["cycle"] for r in ds.fec})
    by_cycle = defaultdict(float)
    for r in ds.fec:
        by_cycle[r["cycle"]] += r["amount"]
    recips = {r["recipient_committee_id"] or r["recipient"] for r in ds.fec}
    ids = [r["evidence_id"] for r in ds.fec][:20]
    cur = ds.as_of.year + (ds.as_of.year % 2)
    trend = "unknown"
    if by_cycle.get(cur - 2):
        trend = "rising" if by_cycle.get(cur, 0) > by_cycle[cur - 2] else "declining"
    return [Check(id="fec:active", question="Affiliated committee disbursed funds this or last cycle?", result=bool(ds.fec),
                  detail=", ".join(map(str, cycles)), evidence_ids=ids),
            Check(id="fec:breadth", question="Supports 10 or more distinct recipient committees?", result=len(recips) >= 10,
                  detail=f"{len(recips)} recipients", evidence_ids=ids)], trend


def _coalitions(ds: Dataset) -> tuple[list[Check], str]:
    aff = {o for r in ds.lda for o in r["affiliated_organizations"]}
    regs = {r["registrant"] for r in ds.lda}
    allies = ds.by_pathway("coalitions_alliances")
    checks = [Check(id="coal:lda_affiliates", question="Lobbying filings list affiliated or co-funding organizations?",
                    result=bool(aff) if ds.lda else None, detail=", ".join(sorted(aff)[:6])),
              Check(id="coal:channels", question="Lobbies through 2 or more registrants (in-house or firms)?",
                    result=len(regs) >= 2 if ds.lda else None, detail=", ".join(sorted(regs)[:6])),
              Check(id="coal:documented", question="Research documents alliances from 3 or more independent sources?",
                    result=independent(allies) >= 3 if ds.research else None, evidence_ids=[e.id for e in allies])]
    return checks + [c for c in _research_checks(ds, "coalitions_alliances") if c.id.endswith("no_verified_damage")], "unknown"


def _media(ds: Dataset) -> tuple[list[Check], str]:
    n = ds.news
    checks = []
    trend = "unknown"
    if n and n.get("volume_recent_90d") is not None and n.get("volume_prior_90d") is not None:
        checks.append(Check(id="media:volume", question="News coverage in the last 90 days at or above the prior 90 days?",
                            result=n["volume_recent_90d"] >= n["volume_prior_90d"], evidence_ids=[n["evidence_id"]]))
        r, p = n["volume_recent_90d"], n["volume_prior_90d"]
        trend = "rising" if r > 1.15 * p else "declining" if r < 0.85 * p else "stable"
    else:
        checks.append(Check(id="media:volume", question="News coverage in the last 90 days at or above the prior 90 days?", result=None))
    tone = n.get("tone_recent_90d") if n else None
    checks.append(Check(id="media:tone", question="Average coverage tone non-negative (GDELT)?",
                        result=None if tone is None else tone >= 0, detail="" if tone is None else f"{tone:+.2f}",
                        evidence_ids=[n["evidence_id"]] if n else []))
    return checks + _research_checks(ds, "media_public_salience"), trend


def _transnational(ds: Dataset) -> tuple[list[Check], str]:
    foreign = {f for r in ds.lda for f in r["foreign_entities"]}
    for_issue = [r for r in ds.lda if "FOR" in r["issue_codes"]]
    checks = [Check(id="intl:foreign_policy", question="Lobbies on foreign relations or discloses foreign entities?",
                    result=bool(foreign or for_issue) if ds.lda else None, evidence_ids=[r["evidence_id"] for r in for_issue[:6]],
                    detail=", ".join(sorted(foreign)[:4]))]
    return checks + _research_checks(ds, "transnational_network"), "unknown"


def _legal(ds: Dataset) -> tuple[list[Check], str]:
    rl = [r for r in ds.lda if {"REL", "CIV", "CON"} & set(r["issue_codes"])]
    checks = [Check(id="legal:liberty_advocacy", question="Lobbies on religion, civil-liberties or constitutional issues?",
                    result=bool(rl) if ds.lda else None, evidence_ids=[r["evidence_id"] for r in rl[:6]])]
    return checks + _research_checks(ds, "legal_advocacy"), "unknown"


def _research_only(pid: str) -> Callable[[Dataset], tuple[list[Check], str]]:
    return lambda ds: (_research_checks(ds, pid), "unknown")


EVALUATORS: dict[str, Callable[[Dataset], tuple[list[Check], str]]] = {
    "membership_base": _research_only("membership_base"), "institutional_trust": _research_only("institutional_trust"),
    "institutional_services": _services, "financial_resources": _finance, "federal_partnerships": _federal,
    "legislative_lobbying": _lobbying, "electoral_engagement": _electoral, "coalitions_alliances": _coalitions,
    "legal_advocacy": _legal, "media_public_salience": _media, "digital_reach": _research_only("digital_reach"),
    "transnational_network": _transnational, "land_and_property": _research_only("land_and_property"),
}


def _research_trend(ds: Dataset, pid: str) -> str:
    evs = [e for e in ds.by_pathway(pid) if e.provider == "research-agent"]
    pos = independent([e for e in evs if e.direction == Direction.STRENGTHENS])
    neg = independent([e for e in evs if e.direction == Direction.WEAKENS])
    if pos + neg < 2:
        return "unknown"
    return "strengthening" if pos >= 2 * max(neg, 1) else "weakening" if neg >= 2 * max(pos, 1) else "contested"


def assess(ds: Dataset) -> list[PathwayAssessment]:
    out = []
    for p in PATHWAYS:
        checks, trend = EVALUATORS[p.id](ds)
        if trend == "unknown":
            trend = _research_trend(ds, p.id)
        evald = [c for c in checks if c.result is not None]
        passed = sum(1 for c in evald if c.result)
        strength = round(100 * passed / len(evald), 1) if len(evald) >= 2 else None
        pressures = [e.claim[:200] for e in ds.by_pathway(p.id) if e.direction == Direction.WEAKENS][:4]
        out.append(PathwayAssessment(id=p.id, label=p.label, dimension=p.dimension, strength=strength,
                                     coverage=round(len(evald) / len(checks), 2) if checks else 0.0, trend=trend,
                                     pressures=pressures, checks=checks, modern_levers=list(p.levers)))
    return out


def exposure(pathways: list[PathwayAssessment]) -> list[dict]:
    """Where sustaining influence is most at risk: weak or weakening pathways with enough evidence to say so."""
    rows = []
    for p in pathways:
        if p.strength is None:
            continue
        decline = p.trend in ("declining", "weakening")
        score = (100 - p.strength) * p.coverage + (20 if decline else 0) + 5 * len(p.pressures)
        rows.append({"pathway": p.id, "label": p.label, "exposure": round(score, 1), "strength": p.strength, "trend": p.trend,
                     "pressures": p.pressures, "levers": p.modern_levers})
    return sorted(rows, key=lambda r: r["exposure"], reverse=True)
