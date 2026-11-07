from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from silent_stocks.config import Settings
from silent_stocks.http import CachedHttp

from . import demo, report
from .collect import Sources, collect
from .connectors import FEC_BASE, Awards, Congress, Fec, Lda, News, ProPublica, load_research
from .models import EntityProfile, ResearchDoc

ROOT = Path(__file__).resolve().parent.parent
RESEARCH_DIR = ROOT / "data" / "influence" / "research"
OUT_DIR = ROOT / "reports" / "influence"


def _http(offline: bool) -> CachedHttp:
    s = Settings()
    return CachedHttp(s.cache_dir, s.sec_user_agent, offline=offline)


def cmd_analyze(a) -> int:
    prof = EntityProfile.model_validate(json.loads(Path(a.profile).read_text()))
    as_of = date.fromisoformat(a.as_of) if a.as_of else report.today()
    http = _http(a.offline)
    src = Sources(Lda(http), ProPublica(http), Fec(http), Awards(http), None if a.no_news else News(http), Congress(http))
    rpath = Path(a.research) if a.research else RESEARCH_DIR / f"{prof.slug}.json"
    ds = collect(prof, as_of, src, load_research(rpath, as_of))
    if ds.research is None:
        ds.gaps.append(f"no research file at {rpath}; research-dependent checks are UNKNOWN")
    r = report.build(ds)
    md, js = report.write(r, Path(a.out))
    print(json.dumps({"markdown": str(md), "json": str(js), "coverage": r["coverage"], "leading_posture": r["sat"]["ach"]["leading"],
                      "top_outlook": [(s["label"], s["score"]) for s in r["sponsorship_outlook"][:5]], "gaps": r["gaps"]}, indent=2))
    return 0


def cmd_demo(a) -> int:
    r = report.build(demo.dataset(date.fromisoformat(a.as_of) if a.as_of else report.today()), demo=True)
    md, _ = report.write(r, Path(a.out))
    print(md.read_text())
    return 0


def cmd_find(a) -> int:
    """Candidate identifiers for building a profile. Every match must be verified by a person before use."""
    http = _http(False)
    out: dict = {"query": a.name}
    out["nonprofits"] = ProPublica(http).search(a.name)[:15]
    data, _ = http.get_json("https://lda.senate.gov/api/v1/clients/", params={"client_name": a.name, "page_size": 25})
    out["lda_clients"] = sorted({c["name"] for c in data.get("results", [])})
    data, _ = http.get_json("https://lda.senate.gov/api/v1/registrants/", params={"registrant_name": a.name, "page_size": 25})
    out["lda_registrants"] = sorted({c["name"] for c in data.get("results", [])})
    fec = Fec(http)
    data, _ = http.get_json(f"{FEC_BASE}/committees/", params={"q": a.name, "per_page": 20, "api_key": fec.api_key})
    out["fec_committees"] = [{"id": c["committee_id"], "name": c["name"], "type": c.get("committee_type_full"),
                              "cycles": (c.get("cycles") or [])[-3:]} for c in data.get("results", [])]
    print(json.dumps(out, indent=2))
    return 0


def cmd_validate_research(a) -> int:
    errors = []
    try:
        doc = ResearchDoc.model_validate(json.loads(Path(a.path).read_text()))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    items = [*doc.findings, *doc.initiatives, *doc.alliances, *doc.policy_windows]
    for it in items:
        if not it.source_url.startswith("http"):
            errors.append(f"non-http source: {it.source_url}")
    if len(doc.findings) < 8:
        errors.append(f"only {len(doc.findings)} findings; need at least 8")
    if not {"strengthens", "weakens"} <= {f.direction.value for f in doc.findings}:
        errors.append("findings must include both strengthening and weakening evidence")
    print(json.dumps({"ok": not errors, "errors": errors, "counts": {"findings": len(doc.findings), "initiatives": len(doc.initiatives),
                                                                    "alliances": len(doc.alliances), "policy_windows": len(doc.policy_windows)}}, indent=2))
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING)
    p = argparse.ArgumentParser(prog="influence-intel")
    sub = p.add_subparsers(dest="cmd", required=True)
    an = sub.add_parser("analyze", help="brief for one entity profile")
    an.add_argument("profile")
    an.add_argument("--as-of")
    an.add_argument("--research")
    an.add_argument("--offline", action="store_true")
    an.add_argument("--no-news", action="store_true")
    an.add_argument("--out", default=str(OUT_DIR))
    an.set_defaults(fn=cmd_analyze)
    d = sub.add_parser("demo", help="offline demo on synthetic fixtures")
    d.add_argument("--as-of")
    d.add_argument("--out", default=str(OUT_DIR))
    d.set_defaults(fn=cmd_demo)
    f = sub.add_parser("find", help="candidate EINs, LDA names and FEC committees for a name")
    f.add_argument("name")
    f.set_defaults(fn=cmd_find)
    v = sub.add_parser("validate-research", help="validate a research subagent file")
    v.add_argument("path")
    v.set_defaults(fn=cmd_validate_research)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
