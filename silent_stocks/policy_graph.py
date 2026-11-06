"""International policy transmission graph.

Country -> Policy (stage) -> Industry -> Bottleneck -> Company -> Revenue mechanism -> Earnings / valuation impact.

A company edge exists only when a sourced, company-specific link exists (research-agent policy_links). Sector-level
policy events are kept as context but never converted into company revenue by inference.
"""
from __future__ import annotations

from .connectors.research import AgentFindings, PolicyEvent
from .models import Evidence, EvidenceType, PolicyChain

INDUSTRY_MAP = {
    "aerospace & defense": {"defense"},
    "semiconductors": {"semiconductors"},
    "electronic components": {"electronic_components"},
    "electronic production equipment": {"electronic_components", "semiconductors"},
    "electrical products": {"energy_storage", "batteries", "grid"},
    "building products": {"grid", "utilities"},
    "telecommunications equipment": {"drones", "electronic_components"},
    "trucks/construction/farm machinery": {"marine", "industrial_power_transmission"},
    "information technology services": {"data_center_power", "ai_infrastructure"},
    "engineering & construction": {"grid", "data_center_power"},
    "industrial machinery": {"semiconductors"},
}


def _tags(text: str) -> set[str]:
    t = text.lower()
    vocab = ["defense", "drone", "counter_drone", "counter-drone", "grid", "transmission", "data center", "data_center",
             "energy storage", "energy_storage", "batter", "critical mineral", "critical_minerals", "semiconductor",
             "electronic", "shipbuild", "marine", "sonar", "subsea", "ai", "utilit", "power"]
    canon = {"drone": "drones", "counter-drone": "counter_drone", "data center": "data_center_power", "data_center": "data_center_power",
             "energy storage": "energy_storage", "batter": "batteries", "critical mineral": "critical_minerals",
             "semiconductor": "semiconductors", "electronic": "electronic_components", "shipbuild": "shipbuilding",
             "subsea": "sonar_subsea", "sonar": "sonar_subsea", "ai": "ai_infrastructure", "utilit": "utilities",
             "power": "data_center_power"}
    out = set()
    for v in vocab:
        if v in t:
            out.add(canon.get(v, v))
    return out


def company_industries(industry: str | None, findings: AgentFindings | None) -> set[str]:
    tags = set(INDUSTRY_MAP.get((industry or "").lower(), set()))
    if findings:
        for link in findings.policy_links:
            tags |= _tags(link.industry) | _tags(link.bottleneck)
    return tags


def build_chains(ticker: str, findings: AgentFindings | None, events: list[PolicyEvent], register) -> list[PolicyChain]:
    chains: list[PolicyChain] = []
    if not findings:
        return chains
    for link in findings.policy_links:
        ev = register(Evidence(
            ticker=ticker, claim=f"{link.country}: {link.policy} -> {link.revenue_mechanism or 'mechanism unspecified'}",
            source_url=link.source_url, published_date=link.published_date,
            evidence_type=EvidenceType.VERIFIED if link.evidence_of_company_revenue else EvidenceType.ANALYST_JUDGMENT,
            provider="research-agent", dimension="political", topic="policy"))
        ids = [ev]
        link_tags = _tags(link.industry) | _tags(link.bottleneck) | _tags(link.policy)
        for e in events:
            if e.country.lower()[:4] in link.country.lower() or link.country.lower()[:4] in e.country.lower():
                if link_tags & set(e.industries):
                    ids.append(register(Evidence(
                        claim=f"{e.country}: {e.policy} ({e.stage}, {e.event_date})", source_url=e.source_url,
                        source_title=e.source_title, published_date=e.event_date, evidence_type=EvidenceType.VERIFIED,
                        provider="policy-research", dimension="political", topic="policy")))
        chains.append(PolicyChain(
            country=link.country, policy=link.policy, stage=link.stage, industry=link.industry,
            bottleneck=link.bottleneck, company=ticker, revenue_mechanism=link.revenue_mechanism,
            evidence_of_company_revenue=link.evidence_of_company_revenue,
            earnings_impact=("company revenue evidenced by source; magnitude not quantified" if link.evidence_of_company_revenue
                             else "not established: favorable policy without company revenue evidence"),
            valuation_impact=("supports revenue-growth assumption in base/bull cases" if link.evidence_of_company_revenue
                              else "excluded from valuation inputs"),
            evidence_ids=list(dict.fromkeys(ids)), source_urls=[link.source_url],
        ))
    return chains


def graph(chains: list[PolicyChain], events: list[PolicyEvent]) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def node(kind: str, label: str) -> str:
        nid = f"{kind}:{label}"
        nodes.setdefault(nid, {"id": nid, "kind": kind, "label": label})
        return nid

    for e in events:
        c = node("country", e.country)
        p = node("policy", f"{e.policy} [{e.stage}]")
        edges.append({"from": c, "to": p, "source": e.source_url, "date": str(e.event_date), "direction": e.direction})
        for ind in e.industries:
            edges.append({"from": p, "to": node("industry", ind), "source": e.source_url})
            for b in e.bottlenecks:
                edges.append({"from": node("industry", ind), "to": node("bottleneck", b), "source": e.source_url})
    for ch in chains:
        c = node("country", ch.country)
        p = node("policy", f"{ch.policy} [{ch.stage}]")
        i = node("industry", ch.industry or "unspecified")
        b = node("bottleneck", ch.bottleneck or "unspecified")
        co = node("company", ch.company)
        mech = node("mechanism", ch.revenue_mechanism or "unspecified")
        src = ch.source_urls[0] if ch.source_urls else ""
        for a, z in ((c, p), (p, i), (i, b), (b, co), (co, mech)):
            edges.append({"from": a, "to": z, "source": src, "company_revenue_evidenced": ch.evidence_of_company_revenue})
    return {"nodes": list(nodes.values()), "edges": edges}
