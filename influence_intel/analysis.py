"""STEMPLE dimension assessment and structured analytic techniques for an organization's strategic posture."""
from __future__ import annotations

from .collect import Dataset, lda_quarters, latest_qkey
from .models import DIMENSIONS, Direction, EvidenceType, PathwayAssessment, SponsorshipCandidate
from .pathways import independent

POSTURES = {
    "H1": "Expansion: growing resources and widening public-policy engagement",
    "H2": "Consolidation: stable resources, defending a core issue set",
    "H3": "Retrenchment: shrinking resources or salience, narrowing engagement",
    "H4": "Realignment: shifting issues or partners while resources hold",
}
# +1 consistent, -1 inconsistent, 0 neutral, applied when the indicator is True; the negated row applies when False.
ACH = {
    "lobby_spend_rising": {"H1": 1, "H2": 0, "H3": -1, "H4": 0},
    "issue_set_widening": {"H1": 1, "H2": -1, "H3": -1, "H4": 1},
    "issue_set_turnover": {"H1": 0, "H2": -1, "H3": 0, "H4": 1},
    "revenue_growing": {"H1": 1, "H2": 0, "H3": -1, "H4": 0},
    "media_rising": {"H1": 1, "H2": 0, "H3": -1, "H4": 0},
    "membership_weakening": {"H1": -1, "H2": 0, "H3": 1, "H4": 1},
}


def stemple(ds: Dataset, pathways: list[PathwayAssessment]) -> list[dict]:
    out = []
    for dim in DIMENSIONS:
        evs = [e for e in ds.evidence.values() if e.dimension == dim]
        pos = [e for e in evs if e.direction == Direction.STRENGTHENS]
        neg = [e for e in evs if e.direction == Direction.WEAKENS]
        ip, ineg = independent(pos), independent(neg)
        strengths = [p.strength for p in pathways if p.dimension == dim and p.strength is not None]
        if ip + ineg == 0 and not strengths:
            label = "insufficient"
        elif ip >= 2 * max(ineg, 1) and ip >= 2:
            label = "tailwind"
        elif ineg >= 2 * max(ip, 1) and ineg >= 2:
            label = "headwind"
        else:
            label = "mixed" if ip + ineg else "structural-data-only"
        top = sorted(pos + neg, key=lambda e: (e.evidence_type == EvidenceType.VERIFIED, e.published_date or ds.as_of), reverse=True)[:3]
        regions = sorted({t for e in evs for t in e.tags if e.provider == "research-agent" and t})
        out.append({"dimension": dim, "assessment": label, "strengthening_sources": ip, "weakening_sources": ineg,
                    "pathway_strength_avg": round(sum(strengths) / len(strengths), 1) if strengths else None,
                    "regions": regions, "summary": "; ".join(e.claim[:140] for e in top) or "No directional evidence",
                    "evidence_ids": [e.id for e in evs][:30]})
    return out


def _indicators(ds: Dataset, pathways: list[PathwayAssessment]) -> dict[str, bool | None]:
    by = {p.id: p for p in pathways}
    q = lda_quarters(ds)
    L = latest_qkey(ds)
    i4 = {c for k in range(L - 3, L + 1) for r in q.get(k, []) for c in r["issue_codes"]}
    ip = {c for k in range(L - 7, L - 3) for r in q.get(k, []) for c in r["issue_codes"]}
    spend = next((c for c in by["legislative_lobbying"].checks if c.id == "lobby:spend_trend"), None)
    rev = next((c for c in by["financial_resources"].checks if c.id == "fin:revenue_growth"), None)
    media = next((c for c in by["media_public_salience"].checks if c.id == "media:volume"), None)
    mem = by["membership_base"].trend
    return {
        "lobby_spend_rising": spend.result if spend else None,
        "issue_set_widening": (len(i4) > len(ip)) if (i4 and ip) else None,
        "issue_set_turnover": (len(i4 ^ ip) >= 2) if (i4 and ip) else None,
        "revenue_growing": rev.result if rev else None,
        "media_rising": media.result if media else None,
        "membership_weakening": None if mem == "unknown" else mem == "weakening",
    }


def ach(ds: Dataset, pathways: list[PathwayAssessment]) -> dict:
    ind = _indicators(ds, pathways)
    inconsistency = {h: 0 for h in POSTURES}
    for k, v in ind.items():
        if v is None:
            continue
        for h, s in ACH[k].items():
            if (s if v else -s) < 0:
                inconsistency[h] += 1
    evaluated = sum(v is not None for v in ind.values())
    low = min(inconsistency.values())
    tied = sorted(h for h, v in inconsistency.items() if v == low)
    leading = tied[0] if evaluated >= 2 and len(tied) == 1 else None
    note = "ACH ranks hypotheses by how much evidence contradicts them; it is analyst judgment, not probability."
    if evaluated < 2:
        note += " Fewer than 2 indicators evaluated, so no hypothesis is preferred."
    elif len(tied) > 1:
        note += f" Tie between {', '.join(tied)}; collect the missing indicators before preferring one."
    return {"hypotheses": POSTURES, "indicators": ind, "inconsistency": inconsistency, "leading": leading,
            "tied": tied if evaluated >= 2 and len(tied) > 1 else [], "note": note}


def key_assumptions(ds: Dataset, pathways: list[PathwayAssessment]) -> list[dict]:
    by = {p.id: p for p in pathways}
    cont = next((c for c in by["legislative_lobbying"].checks if c.id == "lobby:continuity"), None)
    latest_990 = max((rows[-1]["year"] for rows in ds.nonprofit.values() if rows), default=None)
    return [
        {"assumption": "Past disclosed lobbying predicts the next sponsorship focus",
         "status": "supported" if cont and cont.result else "unsupported" if cont and cont.result is False else "untested",
         "basis": cont.detail if cont else "no LDA data"},
        {"assumption": "Disclosed activity represents the whole organization",
         "status": "doubtful" if ds.profile.is_church_exempt_from_lda else "untested",
         "basis": "church bodies are LDA-exempt; 501(c)(3)s cannot campaign; giving by individual members is not attributed"},
        {"assumption": "Financial data are current",
         "status": "untested" if latest_990 is None else "supported" if ds.as_of.year - latest_990 <= 2 else "stale",
         "basis": f"latest public Form 990 FY{latest_990}" if latest_990 else "no Form 990 data"},
        {"assumption": "The news query matches this organization and not namesakes",
         "status": "untested", "basis": f"query: {ds.profile.news_query!r}; verify a sample of articles"},
    ]


def red_team(analysis_ach: dict) -> list[str]:
    lead = analysis_ach["leading"]
    if analysis_ach.get("tied"):
        return [f"No single posture survives: {', '.join(analysis_ach['tied'])} are equally consistent with the evidence."]
    if not lead:
        return ["Evidence too thin to favour any posture; the strongest counter-case is that the data gaps hide the real activity."]
    out = []
    for k, v in analysis_ach["indicators"].items():
        if v is None:
            continue
        s = ACH[k][lead] if v else -ACH[k][lead]
        if s < 0:
            out.append(f"{k}={v} contradicts {lead}")
    alt = sorted((h for h in POSTURES if h != lead), key=lambda h: analysis_ach["inconsistency"][h])[0]
    out.append(f"Closest alternative is {alt} ({POSTURES[alt].split(':')[0]}), with {analysis_ach['inconsistency'][alt]} "
               f"contradictions vs {analysis_ach['inconsistency'][lead]}")
    return out


def premortem(ds: Dataset, outlook: list[SponsorshipCandidate]) -> list[str]:
    out = ["Undisclosed channels (church-exempt lobbying, member-level giving, dark-money vehicles) carry the real priorities",
           "A leadership change or doctrinal decision re-sets priorities faster than quarterly filings reveal",
           "A court ruling or regulation (tax exemption, funding eligibility) forces a defensive pivot"]
    if not outlook:
        out.insert(0, "No revealed-preference data: the outlook is empty, not negative")
    elif all(c.providers == ["senate-lda"] for c in outlook[:5]):
        out.insert(0, "Top outlook items rest on one source type (LDA); none are corroborated by announcements or policy windows")
    out += [g for g in ds.gaps if "unavailable" in g][:4]
    return out


def signposts(outlook: list[SponsorshipCandidate], pathways: list[PathwayAssessment]) -> list[str]:
    s = [sp for c in outlook[:6] for sp in c.signposts[:1]]
    s += [f"{p.label}: watch for reversal of the {p.trend} trend" for p in pathways if p.trend in ("declining", "weakening")]
    return list(dict.fromkeys(s))
