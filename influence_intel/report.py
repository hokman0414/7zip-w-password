from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import analysis, pathways, sponsorship
from .collect import Dataset


def build(ds: Dataset, demo: bool = False) -> dict:
    pw = pathways.assess(ds)
    outlook = sponsorship.candidates(ds)
    a = analysis.ach(ds, pw)
    return {
        "entity": ds.profile.model_dump(mode="json"),
        "as_of": ds.as_of.isoformat(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "demo": demo,
        "executor": "rule-based checks over public records and sourced research (not independent agents)",
        "coverage": {"lda_filings": len(ds.lda), "form_990_years": sum(len(v) for v in ds.nonprofit.values()),
                     "fec_disbursements": len(ds.fec), "federal_awards": len(ds.awards), "news": ds.news is not None,
                     "research_findings": len(ds.research.findings) if ds.research else 0,
                     "research_initiatives": len(ds.research.initiatives) if ds.research else 0},
        "stemple": analysis.stemple(ds, pw),
        "pathways": [p.model_dump(mode="json") for p in pw],
        "exposure": pathways.exposure(pw),
        "sponsorship_outlook": [c.model_dump(mode="json") for c in outlook],
        "lobbied_bills_enacted": sponsorship.recent_wins(ds),
        "sat": {"ach": a, "key_assumptions": analysis.key_assumptions(ds, pw), "red_team": analysis.red_team(a),
                "premortem": analysis.premortem(ds, outlook), "signposts": analysis.signposts(outlook, pw)},
        "gaps": ds.gaps,
        "evidence": {k: v.model_dump(mode="json") for k, v in ds.evidence.items()},
    }


def _fmt(v) -> str:
    return "n/a" if v is None else f"{v:.0f}"


def markdown(r: dict) -> str:
    e = r["entity"]
    L = [f"# Influence brief: {e['name']}" + (" (DEMO, synthetic fixtures)" if r["demo"] else ""), "",
         f"As of {r['as_of']} | generated {r['generated_at']} | {r['executor']}", ""]
    L += ["> Institution-level analysis of public records. Scores rank evidence-backed continuity; they are not",
          "> probabilities. UNKNOWN checks are excluded, never counted as passes. Individual donors and members are not profiled.", ""]
    c = r["coverage"]
    L += ["## Coverage", "", " | ".join(f"{k}: {v}" for k, v in c.items()), ""]
    a = r["sat"]["ach"]
    L += ["## Strategic posture (ACH)", "",
          f"Leading: **{a['leading'] or ('tie: ' + ', '.join(a['tied']) if a['tied'] else 'none')}**"
          + (f" - {a['hypotheses'][a['leading']]}" if a["leading"] else ""),
          f"Contradictions per hypothesis: {a['inconsistency']}", "", a["note"], ""]
    L += ["## Influence pathways", "", "| Pathway | STEMPLE | Strength | Coverage | Trend | Pressures |", "|---|---|---|---|---|---|"]
    for p in r["pathways"]:
        L.append(f"| {p['label']} | {p['dimension']} | {_fmt(p['strength'])} | {p['coverage']:.0%} | {p['trend']} | {len(p['pressures'])} |")
    L += ["", "## Most exposed pathways and modern levers", "",
          "Levers are lawful, transparent options to test against the evidence (analyst judgment, not findings).", ""]
    for x in r["exposure"][:5]:
        L.append(f"- **{x['label']}** (exposure {x['exposure']}, strength {x['strength']:.0f}, {x['trend']})")
        for pr in x["pressures"][:2]:
            L.append(f"  - pressure: {pr}")
        for lv in x["levers"]:
            L.append(f"  - lever: {lv}")
    L += ["", "## Next-sponsorship outlook", "", "| # | Candidate | Kind | Index | Basis | Sources |", "|---|---|---|---|---|---|"]
    for n, s in enumerate(r["sponsorship_outlook"], 1):
        L.append(f"| {n} | {s['label']} | {s['kind']} | {s['score']:.0f} | {'; '.join(s['basis'])[:180]} | {', '.join(s['providers'])} |")
    if not r["sponsorship_outlook"]:
        L.append("| - | No revealed-preference data | | | | |")
    L += ["", "LDA filings do not disclose whether the organization supports or opposes a bill; the outlook says where it will "
          "engage, not which side it takes."]
    if r["lobbied_bills_enacted"]:
        L += ["", "### Lobbied bills that became law (position not disclosed)", ""]
        L += [f"- [{b['bill']}]({b['url']}) {b['title'] or ''} - Public Law {b['public_law']} ({b['date']})"
              + (f"; superseded companions: {', '.join(b['superseded_companions'])}" if b["superseded_companions"] else "")
              for b in r["lobbied_bills_enacted"]]
    L += ["", "## STEMPLE", "", "| Dimension | Assessment | +src | -src | Summary |", "|---|---|---|---|---|"]
    for s in r["stemple"]:
        L.append(f"| {s['dimension']} | {s['assessment']} | {s['strengthening_sources']} | {s['weakening_sources']} | {s['summary'][:160]} |")
    sat = r["sat"]
    L += ["", "## Key assumptions", ""] + [f"- {k['assumption']}: **{k['status']}** ({k['basis']})" for k in sat["key_assumptions"]]
    L += ["", "## Red team", ""] + [f"- {x}" for x in sat["red_team"]]
    L += ["", "## Premortem", ""] + [f"- {x}" for x in sat["premortem"]]
    L += ["", "## Signposts to watch", ""] + [f"- {x}" for x in sat["signposts"]]
    L += ["", "## Data gaps", ""] + [f"- {g}" for g in r["gaps"]] + [""]
    return "\n".join(L)


def write(r: dict, out_dir: Path) -> tuple[Path, Path]:
    d = out_dir / r["entity"]["slug"]
    d.mkdir(parents=True, exist_ok=True)
    stem = r["as_of"] + ("-demo" if r["demo"] else "")
    md, js = d / f"{stem}.md", d / f"{stem}.json"
    md.write_text(markdown(r))
    js.write_text(json.dumps(r, indent=2, default=str))
    return md, js


def today() -> date:
    return datetime.now(ZoneInfo("America/New_York")).date()
