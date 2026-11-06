"""STEMPLE dimension assessments: Social, Technological, Economic, Military, Political, Legal, Environmental."""
from __future__ import annotations

from .context import CompanyContext
from .models import DimensionAssessment, Sentiment

DIMENSIONS = ["social", "technological", "economic", "military", "political", "legal", "environmental"]
REGIONS = ["United States", "China", "EU", "Japan", "South Korea", "Taiwan", "India", "Canada", "Australia"]


def _region_hits(text: str) -> set[str]:
    t = text.lower()
    out = set()
    aliases = {"United States": ("united states", "u.s.", "us "), "EU": ("eu", "europe", "nato"), "South Korea": ("korea",)}
    for r in REGIONS:
        keys = aliases.get(r, (r.lower(),))
        if any(k in t for k in keys):
            out.add(r)
    return out


def assess(ctx: CompanyContext) -> list[DimensionAssessment]:
    out = []
    fin = ctx.fundamentals.evidence if ctx.fundamentals else {}
    for dim in DIMENSIONS:
        evs = [e for e, r in ctx.finding_ev if r.get("dimension") == dim]
        if dim == "economic":
            evs += list(fin.values())
        if dim == "legal":
            evs += [e for e in ctx.evidence.values() if e.provider == "sec-edgar-fts"]
            if ctx.fundamentals and "dilution_yoy" in fin:
                evs.append(fin["dilution_yoy"])
        if dim == "political":
            evs += [ctx.evidence[i] for ch in ctx.policy_chains for i in ch.evidence_ids if i in ctx.evidence]
        if dim == "military":
            evs += [e for e in ctx.evidence.values() if e.provider == "usaspending"]
        evs = list({e.id: e for e in evs}.values())
        pos = sum(e.sentiment == Sentiment.POSITIVE for e in evs)
        neg = sum(e.sentiment == Sentiment.NEGATIVE for e in evs)
        ver = sum(e.evidence_type.value == "verified" for e in evs)
        if not evs or (pos + neg) == 0:
            label = "insufficient"
        elif pos >= 2 * max(neg, 1) and pos >= 2:
            label = "supportive"
        elif neg >= 2 * max(pos, 1) and neg >= 2:
            label = "adverse"
        else:
            label = "mixed"
        regions = set()
        for e in evs:
            regions |= _region_hits(e.claim)
        if dim == "political":
            for ch in ctx.policy_chains:
                regions |= _region_hits(ch.country) or {ch.country}
        top = sorted(evs, key=lambda e: (e.sentiment != Sentiment.NEUTRAL, e.published_date or ctx.as_of.date()), reverse=True)[:3]
        summary = "; ".join(e.claim[:140] for e in top) if top else "No evidence retrieved for this dimension"
        out.append(DimensionAssessment(dimension=dim, assessment=label, summary=summary, positive=pos, negative=neg,
                                       verified=ver, evidence_ids=[e.id for e in evs], regions=sorted(regions)))
    return out
