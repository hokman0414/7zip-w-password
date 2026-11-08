"""Turns raw public records into a point-in-time Dataset with a cited evidence registry."""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date

from silent_stocks.http import HttpError

from .connectors import Awards, Congress, Fec, Lda, News, ProPublica
from .models import LDA_ISSUES, Direction, EntityProfile, Evidence, EvidenceType, ResearchDoc

log = logging.getLogger(__name__)


@dataclass
class Sources:
    lda: Lda | None = None
    propublica: ProPublica | None = None
    fec: Fec | None = None
    awards: Awards | None = None
    news: News | None = None
    congress: Congress | None = None


@dataclass
class Dataset:
    profile: EntityProfile
    as_of: date
    lda: list[dict] = field(default_factory=list)
    nonprofit: dict[str, list[dict]] = field(default_factory=dict)
    fec: list[dict] = field(default_factory=list)
    awards: list[dict] = field(default_factory=list)
    news: dict | None = None
    bills: dict[str, dict] = field(default_factory=dict)
    research: ResearchDoc | None = None
    evidence: dict[str, Evidence] = field(default_factory=dict)
    initiative_ev: dict[int, str] = field(default_factory=dict)
    subgroup_ev: dict[str, str] = field(default_factory=dict)
    gaps: list[str] = field(default_factory=list)

    def add(self, ev: Evidence) -> str:
        self.evidence[ev.id] = ev
        return ev.id

    def by_pathway(self, pathway: str) -> list[Evidence]:
        return [e for e in self.evidence.values() if pathway in e.pathways]


def _try(label: str, gaps: list[str], fn, default):
    try:
        return fn()
    except (HttpError, FileNotFoundError, ValueError, KeyError) as exc:
        log.warning("%s failed: %s", label, exc)
        gaps.append(f"{label} unavailable: {exc}")
        return default


def collect(profile: EntityProfile, as_of: date, src: Sources, research: ResearchDoc | None = None, max_bills: int = 40) -> Dataset:
    ds = Dataset(profile=profile, as_of=as_of, research=research)
    for aff in profile.affiliates:
        if src.lda and (aff.lda_client_names or aff.lda_registrant_names):
            ds.lda += _try(f"LDA filings for {aff.name}", ds.gaps,
                           lambda: src.lda.filings(as_of, client_names=aff.lda_client_names, registrant_names=aff.lda_registrant_names), [])
        if src.propublica and aff.ein:
            ds.nonprofit[aff.name] = _try(f"Form 990 data for {aff.name}", ds.gaps, lambda: src.propublica.filings(aff.ein, as_of), [])
            if not ds.nonprofit[aff.name]:
                ds.gaps.append(f"no machine-readable Form 990 financials for {aff.name} (EIN {aff.ein}) on ProPublica")
        if src.fec:
            for cid in aff.fec_committee_ids:
                ds.fec += _try(f"FEC disbursements {cid}", ds.gaps, lambda: src.fec.disbursements(cid, as_of), [])
        if src.awards:
            for n in aff.usaspending_names:
                ds.awards += _try(f"USAspending awards for {n}", ds.gaps, lambda: src.awards.search(n, as_of), [])
    ds.lda = list({r["uuid"]: r for r in ds.lda}.values())
    ds.lda.sort(key=lambda r: (r["qkey"], r["uuid"]))
    if src.news and profile.news_query:
        ds.news = _try("GDELT news timeline", ds.gaps, lambda: src.news.summary(profile.news_query, as_of), None)
        if ds.news is None:
            ds.gaps.append("GDELT news timeline unavailable (rate limit or no coverage); media checks are UNKNOWN")
    if src.congress:
        L = latest_qkey(ds)
        recent = [b for b, _ in Counter(b for r in ds.lda if r["qkey"] >= L - 3 for b in r["bills"]).most_common()]
        for key in recent[:max_bills]:
            st = _try(f"congress.gov status {key}", ds.gaps, lambda: src.congress.status(key, as_of), None)
            if st:
                ds.bills[key] = st
        if len(recent) > max_bills:
            ds.gaps.append(f"bill status fetched for {max_bills} of {len(recent)} recently lobbied bills")
    if profile.is_church_exempt_from_lda:
        ds.gaps.append("Churches and conventions of churches are exempt from LDA registration; lobbying by the core body "
                       "may be undisclosed. Only filings by registered affiliates or hired firms are visible.")
    _register(ds)
    return ds


def _register(ds: Dataset) -> None:
    for r in ds.lda:
        codes = ", ".join(LDA_ISSUES.get(c, c) for c in r["issue_codes"]) or "no issue codes"
        amt = f"${r['amount']:,.0f}" if r["amount"] else "amount not reported"
        r["evidence_id"] = ds.add(Evidence(
            provider="senate-lda", claim=f"{r['client']} lobbying via {r['registrant']} in {r['year']} Q{r['quarter']}: {codes} ({amt})"
                                         + (f"; bills: {', '.join(r['bills'][:6])}" if r["bills"] else ""),
            source_url=r["url"], source_title=f"LD-2 {r['filing_type']} {r['year']} Q{r['quarter']}", published_date=r["posted"],
            dimension="political", pathways=["legislative_lobbying"], tags=r["issue_codes"], amount=r["amount"]))
    for name, rows in ds.nonprofit.items():
        for r in rows:
            r["evidence_id"] = ds.add(Evidence(
                provider="irs-990-propublica", claim=f"{name} FY{r['year']}: revenue ${r['revenue'] or 0:,.0f}, "
                                                     f"expenses ${r['expenses'] or 0:,.0f}, assets ${r['assets'] or 0:,.0f}",
                source_url=r["url"], source_title=f"Form 990 FY{r['year']}", published_date=r["period_end"],
                dimension="economic", pathways=["financial_resources", "institutional_services"], amount=r["revenue"]))
    for r in ds.fec:
        r["evidence_id"] = ds.add(Evidence(
            provider="fec", claim=f"Committee {r['committee_id']} disbursed ${r['amount']:,.0f} to {r['recipient']} on {r['date']}"
                                  + (f" ({r['purpose']})" if r["purpose"] else ""),
            source_url=r["url"], source_title=f"FEC Schedule B {r['cycle']}", published_date=r["date"],
            dimension="political", pathways=["electoral_engagement"], amount=r["amount"]))
    for r in ds.awards:
        r["evidence_id"] = ds.add(Evidence(
            provider="usaspending", claim=f"Federal {r['kind']} ${r['amount']:,.0f} from {r['agency']} to {r['recipient']} "
                                          f"(name-matched; verify recipient): {(r['description'] or '')[:120]}",
            source_url=r["url"], source_title=f"USAspending {r['award_id']}", published_date=r["start_date"],
            evidence_type=EvidenceType.REPORTED, dimension="economic", pathways=["federal_partnerships", "institutional_services"],
            amount=r["amount"]))
    for key, b in ds.bills.items():
        if b["latest_action"]:
            b["evidence_id"] = ds.add(Evidence(
                provider="congress-gov", claim=f"{key} {b['title'] or ''}: latest action {b['latest_action_date']} - {b['latest_action']}"[:400],
                source_url=b["url"], source_title=f"congress.gov {key}", published_date=b["latest_action_date"],
                dimension="political", pathways=["legislative_lobbying"]))
    if ds.news:
        n = ds.news
        ds.news["evidence_id"] = ds.add(Evidence(
            provider="gdelt", claim=f"News coverage intensity {n['volume_recent_90d'] or 0:.4f}% of monitored articles (last 90d) vs "
                                    f"{n['volume_prior_90d'] or 0:.4f}% prior 90d; average tone {n['tone_recent_90d'] or 0:+.2f}",
            source_url=n["url"], source_title="GDELT DOC 2.0 timeline", published_date=ds.as_of,
            dimension="social", pathways=["media_public_salience"]))
    if ds.research:
        for f in ds.research.findings:
            ds.add(Evidence(provider="research-agent", claim=f.claim, source_url=f.source_url, source_title=f.source_title,
                            published_date=f.published_date, evidence_type=f.evidence_type, direction=f.direction,
                            dimension=f.dimension, pathways=[f.pathway], tags=[f.region] if f.region else []))
        for a in ds.research.alliances:
            ds.add(Evidence(provider="research-agent", claim=f"Alliance with {a.partner} ({a.kind})", source_url=a.source_url,
                            published_date=a.since, evidence_type=a.evidence_type, direction=Direction.STRENGTHENS,
                            dimension="political", pathways=["coalitions_alliances"]))
        for sg in ds.research.subgroups:
            ds.subgroup_ev[sg.name] = ds.add(Evidence(
                provider="research-agent", claim=f"Subgroup {sg.name} ({sg.kind}): {sg.role}".rstrip(": "),
                source_url=sg.source_url, evidence_type=sg.evidence_type, dimension="political", pathways=list(sg.pathways)))
        for n, i in enumerate(ds.research.initiatives):
            ds.initiative_ev[n] = ds.add(Evidence(
                provider="research-agent", claim=f"Initiative: {i.name} ({i.kind}, {i.stage})", source_url=i.source_url,
                source_title=i.source_title, published_date=i.published_date, evidence_type=i.evidence_type,
                dimension="political", pathways=["sponsorship"], tags=[i.issue_code] if i.issue_code else []))


def lda_quarters(ds: Dataset) -> dict[int, list[dict]]:
    q: dict[int, list[dict]] = defaultdict(list)
    for r in ds.lda:
        q[r["qkey"]].append(r)
    return q


def latest_qkey(ds: Dataset) -> int:
    """Most recent quarter that is fully reportable (LD-2 is due 20 days after quarter end)."""
    y, m = ds.as_of.year, ds.as_of.month
    cur = y * 4 + (m - 1) // 3
    return cur - 1
