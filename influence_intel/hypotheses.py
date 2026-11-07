"""1,000 competing hypotheses about which subgroup supports which target, through which pathway, on which horizon.

Each hypothesis is scored with an Analysis of Competing Hypotheses matrix: a diagnostic is +1 (consistent), -1
(contradicts), 0 (evaluated, neutral) or missing. Missing diagnostics are not evidence. The support index is the
share of evaluated diagnostics that are consistent; it ranks hypotheses and is not a probability. When the real
combination space is larger than 1,000, the 1,000 with the fewest contradictions are kept. When it is smaller, the
report says so rather than inventing subgroups or targets to fill the number.
"""
from __future__ import annotations

import re
from collections import Counter

from .collect import Dataset
from .models import PATHWAY_IDS
from .pathways import PATHWAYS, PathwayAssessment
from .sponsorship import candidates

COUNT = 1000
HORIZONS = ("next_quarter", "next_year", "next_congress")
# Extra horizon is used only when two horizons do not produce 1,000 real combinations.
_MIN_HORIZONS = 2
_LEGAL_SUFFIX = ("incorporated", "corporation", "company", "inc", "llc", "llp", "pllc", "ltd")

# What each kind of unit can credibly do. The national office and unclassified units are not penalised: their range
# is unknown, so the diagnostic is missing. This map is analyst judgment, stated in the brief.
CAPABLE = {
    "member_agency": {"institutional_services", "federal_partnerships", "membership_base", "financial_resources", "land_and_property"},
    "regional_body": {"membership_base", "institutional_services", "legislative_lobbying", "coalitions_alliances"},
    "religious_order": {"membership_base", "institutional_services", "transnational_network", "land_and_property"},
    "advocacy_arm": {"legislative_lobbying", "legal_advocacy", "media_public_salience", "electoral_engagement", "coalitions_alliances"},
    "service_institution": {"institutional_services", "federal_partnerships", "financial_resources", "land_and_property"},
    "foundation": {"financial_resources"},
    "pac": {"electoral_engagement"},
    "lobbying_firm": {"legislative_lobbying", "legal_advocacy"},
    "coalition": {"coalitions_alliances", "legislative_lobbying", "media_public_salience"},
    "international_partner": {"transnational_network", "coalitions_alliances"},
    "governing_body": {"legislative_lobbying", "legal_advocacy", "institutional_trust", "membership_base", "transnational_network"},
}
RELATION = {"core": "national_office", "service": "service_institution", "pac": "pac", "advocacy": "advocacy_arm", "foundation": "foundation"}
LABEL = {p.id: p.label for p in PATHWAYS}
DIAGNOSTICS = ("issue_fit", "target_revealed", "pathway_assigned", "pathway_strength", "pathway_trend",
               "role_can_use_pathway", "horizon_fit", "pathway_not_under_pressure", "evidence_channel")
_HORIZON_RANK = {"next_quarter": 0, "next_year": 1, "next_congress": 2}
# Presentation order inside an evidence tie only. A hired firm acts for the organization, so the organization's own unit is listed first.
_KIND_RANK = {"national_office": 0, "governing_body": 1, "advocacy_arm": 2, "member_agency": 3, "service_institution": 4,
              "regional_body": 5, "religious_order": 6, "pac": 7, "foundation": 8, "coalition": 9,
              "international_partner": 10, "lobbying_firm": 11, "other": 12}


def _key(name: str) -> str:
    s = re.sub(r"[^a-z0-9]", "", name.lower())
    for w in _LEGAL_SUFFIX:
        s = s.replace(w, "")
    return s


def _same(a: str, b: str) -> bool:
    ka, kb = _key(a), _key(b)
    return bool(ka and kb and (ka == kb or ka in kb or kb in ka))


def _actor() -> dict:
    return {"issue_codes": set(), "pathways": set(), "evidence_ids": [], "role": "", "source": "derived"}


def _merge(actors: list[dict], name: str, kind: str, *, prefer: bool = False, **kw) -> dict:
    for a in actors:
        if _same(a["name"], name):
            a["issue_codes"] |= set(kw.get("issue_codes") or [])
            a["pathways"] |= set(kw.get("pathways") or [])
            a["evidence_ids"] += list(kw.get("evidence_ids") or [])
            if prefer:
                a["name"], a["kind"], a["source"] = name, kind, kw.get("source", a["source"])
                a["role"] = kw.get("role") or a["role"]
            return a
    a = _actor() | {"name": name, "kind": kind, "source": kw.get("source", "derived"), "role": kw.get("role", ""),
                    "issue_codes": set(kw.get("issue_codes") or []), "pathways": set(kw.get("pathways") or []),
                    "evidence_ids": list(kw.get("evidence_ids") or [])}
    actors.append(a)
    return a


def subgroups(ds: Dataset) -> list[dict]:
    """The organization, its configured affiliates, LDA registrants and affiliated organizations, plus researched units."""
    actors: list[dict] = []
    _merge(actors, ds.profile.name, "national_office", source="profile")
    for aff in ds.profile.affiliates:
        _merge(actors, aff.name, RELATION.get(aff.relation, "other"), pathways=CAPABLE.get(RELATION.get(aff.relation, ""), set()))
    org = next(a for a in actors if _same(a["name"], ds.profile.name))
    for r in ds.lda:
        if _same(r["client"], ds.profile.name) or any(_same(r["client"], a.name) for a in ds.profile.affiliates):
            org["issue_codes"] |= set(r["issue_codes"])
            org["evidence_ids"].append(r["evidence_id"])
        if not r["in_house"]:
            _merge(actors, r["registrant"], "lobbying_firm", pathways={"legislative_lobbying"},
                   issue_codes=r["issue_codes"], evidence_ids=[r["evidence_id"]], source="lda")
    affiliated = Counter(o for r in ds.lda for o in r["affiliated_organizations"])
    for name, _ in affiliated.most_common(15):
        _merge(actors, name, "other", source="lda", pathways={"coalitions_alliances"})
    if ds.research:
        for sg in ds.research.subgroups:
            _merge(actors, sg.name, sg.kind, prefer=True, source="research", role=sg.role, issue_codes=sg.issue_codes,
                   pathways=sg.pathways, evidence_ids=[ds.subgroup_ev[sg.name]] if sg.name in ds.subgroup_ev else [])
    for a in actors:
        a["issue_codes"] = sorted(a["issue_codes"])
        a["pathways"] = sorted(a["pathways"])
        a["evidence_ids"] = list(dict.fromkeys(a["evidence_ids"]))[:8]
    return actors


def _channels(target) -> tuple[str | None, set[str]]:
    """The pathway the evidence actually records, plus secondary pathways it is consistent with."""
    primary, secondary = None, set()
    if "senate-lda" in target.providers or "congress-gov" in target.providers:
        primary = "legislative_lobbying"
        if set(target.issue_codes) & {"REL", "CIV", "CON"}:
            secondary.add("legal_advocacy")
    if "fec" in target.providers:
        if primary is None:
            primary = "electoral_engagement"
        else:
            secondary.add("electoral_engagement")
    if "research-initiative" in target.providers or "policy-calendar" in target.providers:
        if target.kind in ("program", "institution"):
            secondary.add("institutional_services")
        if target.kind == "media":
            secondary.add("media_public_salience")
        if target.kind == "coalition":
            secondary.add("coalitions_alliances")
        if primary is None:
            primary = {"coalition": "coalitions_alliances", "program": "institutional_services",
                       "institution": "institutional_services", "media": "media_public_salience"}.get(target.kind, "legislative_lobbying")
    return primary, secondary


def _sign(value: bool | None) -> int | None:
    return None if value is None else (1 if value else -1)


def _diagnostics(actor: dict, target, pathway: PathwayAssessment, horizon: str) -> dict[str, int | None]:
    codes = set(target.issue_codes)
    overlap = bool(codes & set(actor["issue_codes"]))
    issue = None if not actor["issue_codes"] or not codes else overlap
    comp = target.components
    revealed = comp.get("persistence", 0) >= 0.5 or comp.get("corroboration", 0) > 0
    assigned = None if not actor["pathways"] else pathway.id in actor["pathways"]
    strength = None if pathway.strength is None else (1 if pathway.strength >= 67 else -1 if pathway.strength <= 33 else 0)
    trend = {"rising": 1, "strengthening": 1, "declining": -1, "weakening": -1, "stable": 0, "contested": 0}.get(pathway.trend)
    capable = CAPABLE.get(actor["kind"])
    role = None if capable is None else pathway.id in capable
    recency = comp.get("recency", 0)
    if horizon == "next_quarter":
        horizon_fit = recency >= 1 or comp.get("momentum", 0) >= 1
    elif horizon == "next_year":
        horizon_fit = recency >= 0.5 or comp.get("persistence", 0) >= 0.5
    else:
        horizon_fit = comp.get("persistence", 0) > 0 or recency > 0
    pressure = None if pathway.strength is None and not pathway.pressures else not pathway.pressures
    primary, secondary = _channels(target)
    if primary is None and not secondary:
        channel = None
    elif pathway.id == primary:
        channel = 1
    elif pathway.id in secondary:
        channel = 0
    else:
        channel = -1
    return {"issue_fit": _sign(issue), "target_revealed": 1 if revealed else -1, "pathway_assigned": _sign(assigned),
            "pathway_strength": strength, "pathway_trend": trend, "role_can_use_pathway": _sign(role),
            "horizon_fit": 1 if horizon_fit else -1, "pathway_not_under_pressure": _sign(pressure),
            "evidence_channel": channel}


def _score(diag: dict[str, int | None]) -> tuple[int, float | None, int]:
    vals = [v for v in diag.values() if v is not None]
    minus = sum(v < 0 for v in vals)
    if len(vals) < 2:
        return minus, None, len(vals)
    return minus, round(100 * sum(v > 0 for v in vals) / len(vals), 1), len(vals)


def _red_team(diag: dict[str, int | None], target) -> str:
    neg = [k for k, v in diag.items() if v is not None and v < 0]
    missing = [k for k, v in diag.items() if v is None]
    text = f"Contradicted by {', '.join(neg)}." if neg else "No evaluated diagnostic contradicts it."
    if missing:
        text += f" Not tested: {', '.join(missing)}."
    if "senate-lda" in target.providers:
        text += " Lobbying filings show engagement, not support or opposition."
    return text


def _assumptions(actor: dict, target) -> list[str]:
    out = []
    if "senate-lda" in target.providers:
        out.append("past disclosed lobbying predicts the next focus")
    if actor["kind"] == "lobbying_firm":
        out.append("a hired firm continues the issues it was paid to lobby")
    if actor["source"] != "research":
        out.append("this unit is inferred from the profile or a filing, not from a researched subgroup list")
    return out


def _fragile(diag: dict[str, int | None]) -> list[str]:
    """A hypothesis is fragile to a diagnostic when removing that one consistent result drops its support by 25 points
    or creates a contradiction it did not have."""
    base_minus, base_support, _ = _score(diag)
    if base_support is None:
        return []
    out = []
    for k, v in diag.items():
        if v != 1:
            continue
        alt = dict(diag) | {k: 0}
        minus, support, _ = _score(alt)
        if minus > base_minus or (support is not None and base_support - support >= 25):
            out.append(k)
    return out


def _evidence_key(h: dict) -> tuple:
    return (h["support"] is None, h["inconsistency"], -(h["support"] or 0), -h["target_score"])


def _rank(h: dict) -> tuple:
    # Kind and horizon only order an evidence tie. Neither is extra evidence.
    return _evidence_key(h) + (_KIND_RANK.get(h["subgroup_kind"], 12), _HORIZON_RANK[h["horizon"]], h["statement"])


def evaluate(ds: Dataset, pathway_assessments: list[PathwayAssessment]) -> dict:
    targets = candidates(ds, limit=None)
    actors = subgroups(ds)
    by_id = {p.id: p for p in pathway_assessments}
    n_horizons = _MIN_HORIZONS
    built: list[dict] = []
    while True:
        built = [_hypothesis(a, t, by_id[pid], hz)
                 for a in actors for t in targets for pid in PATHWAY_IDS for hz in HORIZONS[:n_horizons]]
        if len(built) >= COUNT or n_horizons == len(HORIZONS) or not built:
            break
        n_horizons += 1
    built.sort(key=_rank)
    kept = built[:COUNT]
    for n, h in enumerate(kept, 1):
        h["id"] = f"H{n:04d}"
    leader = kept[0] if kept else None
    tie = [h for h in kept if leader and _evidence_key(h) == _evidence_key(leader)]
    by_subgroup: list[dict] = []
    for a in actors:
        mine = [h for h in kept if h["subgroup"] == a["name"]]
        best = mine[0] if mine else None
        by_subgroup.append({
            "name": a["name"], "kind": a["kind"], "source": a["source"], "role": a["role"],
            "issue_codes": a["issue_codes"], "pathways": a["pathways"], "hypotheses_retained": len(mine),
            "best": None if not best else {"id": best["id"], "statement": best["statement"], "support": best["support"],
                                            "inconsistency": best["inconsistency"], "red_team": best["red_team"]},
            "sat": {"technique": "ACH diagnostics + key assumptions + red team + sensitivity",
                    "status": "untested" if not best or best["support"] is None else "supported" if best["inconsistency"] == 0 else "contested"},
        })
    return {
        "method": ("Each hypothesis states that one subgroup supports one target through one influence pathway on one "
                   "horizon. Nine ACH diagnostics score it +1, -1, 0 or missing; missing is ignored. The evidence-channel "
                   "diagnostic is +1 only for the pathway the source records (a lobbying filing for legislative advocacy, "
                   "an FEC disbursement for electoral activity) and -1 for a pathway the source does not record. Support "
                   "is the percentage of evaluated diagnostics that are consistent, and it is not a probability. "
                   f"Generated {len(built)} from {len(actors)} subgroups, {len(targets)} targets and {n_horizons} horizons; "
                   f"retained {len(kept)}."),
        "generated": len(built), "retained": len(kept), "subgroups_analyzed": len(actors), "targets_analyzed": len(targets),
        "horizons_used": list(HORIZONS[:n_horizons]),
        "shortfall": None if len(built) >= COUNT else (
            "No sponsorship targets are in evidence, so no hypothesis is stated." if not targets else
            f"Only {len(built)} hypotheses can be stated from the sourced subgroups and targets. No hypotheses were invented to reach {COUNT}."),
        "most_supported": None if not leader else {
            "tied_count": len(tie), "hypotheses": [{k: h[k] for k in ("id", "statement", "support", "inconsistency", "fragile")} for h in tie[:5]],
            "note": ("These hypotheses are equally consistent with the evidence. Within the tie, the organization's own "
                     "unit is listed before a hired firm, and the nearer horizon before the later one." if len(tie) > 1 else
                     "This hypothesis has the fewest contradictions and the highest support."),
        },
        "by_subgroup": by_subgroup,
        "hypotheses": kept,
    }


def _hypothesis(actor: dict, target, pathway: PathwayAssessment, horizon: str) -> dict:
    diag = _diagnostics(actor, target, pathway, horizon)
    minus, support, evaluated = _score(diag)
    when = {"next_quarter": "the next quarter", "next_year": "the next year", "next_congress": "the next two years"}[horizon]
    return {
        "statement": f"{actor['name']} ({actor['kind']}) supports {target.label} through {LABEL[pathway.id]} within {when}.",
        "subgroup": actor["name"], "subgroup_kind": actor["kind"], "subgroup_source": actor["source"],
        "target": target.label, "target_kind": target.kind, "target_score": target.score,
        "pathway": pathway.id, "horizon": horizon, "support": support, "inconsistency": minus, "evaluated": evaluated,
        "diagnostics": diag, "assumptions": _assumptions(actor, target), "red_team": _red_team(diag, target),
        "fragile": _fragile(diag), "evidence_ids": list(dict.fromkeys(actor["evidence_ids"] + target.evidence_ids))[:12],
    }
