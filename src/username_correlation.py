"""Username correlation across public indexes — no private-person profiling."""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now

USERNAME_VARIANTS = [
    "royalediamondslive",
    "RoyaleDiamondsLive",
    "royale_diamonds",
    "royalediamonds",
    "RoyaleDiamonds",
]


def build_attribution_graph(nodes: list[dict], edges: list[dict]) -> dict:
    g = nx.DiGraph()
    for n in nodes:
        g.add_node(n["id"], **n)
    for e in edges:
        g.add_edge(e["source"], e["target"], **{k: v for k, v in e.items() if k not in {"source", "target"}})
    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": g.number_of_nodes(),
        "edge_count": g.number_of_edges(),
    }


def correlate_usernames(
    primary_username: str = "royalediamondslive",
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "tiktok"
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes = [
        {
            "id": "tiktok:royalediamondslive",
            "platform": "tiktok",
            "username": "royalediamondslive",
            "confidence": "HIGH",
            "basis": "Mashable link + live public profile title/bio",
        },
        {
            "id": "instagram:RoyaleDiamondsLive",
            "platform": "instagram",
            "username": "RoyaleDiamondsLive",
            "confidence": "MEDIUM",
            "basis": "Self-asserted in TikTok bio; Instagram web view required login (blocked)",
        },
    ]
    edges = [
        {
            "source": "tiktok:royalediamondslive",
            "target": "instagram:RoyaleDiamondsLive",
            "relation": "bio_claim",
            "confidence": "MEDIUM",
            "note": "Username match alone is not ownership proof; bio claim is self-asserted.",
        }
    ]

    # Probe public profile URLs without auth bypass
    probes = []
    for platform, url in [
        ("instagram", f"https://www.instagram.com/{primary_username}/"),
        ("telegram_tme", f"https://t.me/{primary_username}"),
        ("twitter", f"https://x.com/{primary_username}"),
        ("youtube", f"https://www.youtube.com/@{primary_username}"),
    ]:
        meta = collector.get(url, cache_key=f"uname_{platform}_{primary_username}")
        status = "reachable" if meta.get("http_status") and meta["http_status"] < 400 else "blocked_or_missing"
        title = ""
        if meta.get("content"):
            text = meta["content"].decode("utf-8", errors="ignore")
            m = text.split("<title>")
            if len(m) > 1:
                title = m[1].split("</title>")[0][:200]
        probes.append(
            {
                "platform": platform,
                "url": url,
                "http_status": meta.get("http_status"),
                "status": status,
                "title": title,
                "error": meta.get("error"),
            }
        )
        if platform == "telegram_tme" and meta.get("http_status") == 200 and "tgme" in title.lower() or (
            meta.get("content") and b"tgme_page" in meta.get("content", b"")
        ):
            nodes.append(
                {
                    "id": f"telegram:{primary_username}",
                    "platform": "telegram",
                    "username": primary_username,
                    "confidence": "LOW",
                    "basis": "Public t.me page reachable; ownership not confirmed",
                }
            )
            edges.append(
                {
                    "source": "tiktok:royalediamondslive",
                    "target": f"telegram:{primary_username}",
                    "relation": "username_collision_candidate",
                    "confidence": "LOW",
                    "note": "Do not treat matching username as shared ownership.",
                }
            )

    graph = build_attribution_graph(nodes, edges)
    result = {
        "variants_searched": USERNAME_VARIANTS,
        "probes": probes,
        "graph": graph,
        "collected_at_utc": utc_now().isoformat(),
        "disclaimer": (
            "Matching usernames are correlation candidates only. "
            "No private individuals were identified. No authenticated access attempted."
        ),
    }
    (out_dir / "username_correlation.json").write_text(json.dumps(result, indent=2))
    ledger.append(
        EvidenceRecord(
            evidence_id="username_correlation_graph",
            source_url="local://username_correlation",
            source_title="Username correlation graph",
            source_category="identity",
            reliability=Reliability.C,
            evidence_tier=EvidenceTier.SECONDARY,
            status=ClaimStatus.UNVERIFIED,
            extracted_facts={"node_count": graph["node_count"], "edge_count": graph["edge_count"]},
            notes=result["disclaimer"],
        )
    )
    if owns:
        collector.close()
    return result