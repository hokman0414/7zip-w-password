"""Structured Analytic Techniques: ACH, key assumptions, indicators/signposts, red team, devil's advocacy, premortem,
scenario analysis, cross-impact, Bayesian updating (only with calibrated inputs), sensitivity/Monte Carlo summary."""
from __future__ import annotations

import json
from pathlib import Path

from .context import CompanyContext
from .models import AssignmentResult, RiskVeto, Sentiment, TechniqueOutput, ValuationResult, Vote

HYPOTHESES = {
    "H1": "Undiscovered compounder: fundamentals improving faster than the market is pricing",
    "H2": "Fairly priced: improvement real but already reflected in valuation",
    "H3": "Value trap: low price reflects deteriorating business or financing risk",
    "H4": "Speculative momentum: price driven by narrative ahead of fundamentals",
}


def _indicators(ctx: CompanyContext, val: ValuationResult) -> dict[str, bool | None]:
    m = ctx.fundamentals.metrics if ctx.fundamentals else {}
    md = ctx.market
    neg_ver = sum(1 for e, r in ctx.finding_ev if r["sentiment"] == "negative" and r["evidence_type"] == "verified")
    pos_ver = sum(1 for e, r in ctx.finding_ev if r["sentiment"] == "positive" and r["evidence_type"] == "verified")
    g = m.get("revenue_growth_yoy")
    return {
        "revenue_growth_>=20%": None if g is None else g >= 0.2,
        "margins_expanding": None if m.get("gross_margin_change") is None else m["gross_margin_change"] > 0,
        "fcf_positive": None if m.get("fcf_ttm") is None else m["fcf_ttm"] > 0,
        "cheaper_than_peers": None if not (val.ev_revenue and val.peer_ev_revenue_median) else val.ev_revenue < val.peer_ev_revenue_median,
        "price_up_>100%_12m": None if not md or md.return_12m is None else md.return_12m > 1.0,
        "price_down_>50%_12m": None if not md or md.return_12m is None else md.return_12m < -0.5,
        "dilution_>10%": None if m.get("dilution_yoy") is None else m["dilution_yoy"] > 0.10,
        "negatives_outweigh_positives": None if (pos_ver + neg_ver) == 0 else neg_ver > pos_ver,
    }


# Consistency of each indicator (when True) with each hypothesis: +1 consistent, -1 inconsistent, 0 neutral.
ACH_MATRIX = {
    "revenue_growth_>=20%": {"H1": 1, "H2": 1, "H3": -1, "H4": 0},
    "margins_expanding": {"H1": 1, "H2": 1, "H3": -1, "H4": 0},
    "fcf_positive": {"H1": 1, "H2": 1, "H3": -1, "H4": -1},
    "cheaper_than_peers": {"H1": 1, "H2": -1, "H3": 1, "H4": -1},
    "price_up_>100%_12m": {"H1": -1, "H2": 1, "H3": -1, "H4": 1},
    "price_down_>50%_12m": {"H1": 0, "H2": -1, "H3": 1, "H4": 1},
    "dilution_>10%": {"H1": -1, "H2": 0, "H3": 1, "H4": 1},
    "negatives_outweigh_positives": {"H1": -1, "H2": 0, "H3": 1, "H4": 1},
}


def ach(ctx: CompanyContext, val: ValuationResult) -> TechniqueOutput:
    ind = _indicators(ctx, val)
    inconsistency = {h: 0 for h in HYPOTHESES}
    matrix = {}
    for k, present in ind.items():
        if present is None:
            matrix[k] = "missing"
            continue
        row = ACH_MATRIX[k]
        matrix[k] = {h: (row[h] if present else -row[h] if row[h] == 1 and k in ("revenue_growth_>=20%", "fcf_positive") else 0) for h in HYPOTHESES}
        for h, s in matrix[k].items():
            if s < 0:
                inconsistency[h] += 1
    best = min(inconsistency, key=inconsistency.get)
    return TechniqueOutput(technique="Analysis of Competing Hypotheses", summary=(
        f"Least-inconsistent hypothesis: {best} ({HYPOTHESES[best]}); inconsistency counts {inconsistency}. "
        "ACH ranks by disconfirming evidence (analyst judgment), not probability."),
        details={"hypotheses": HYPOTHESES, "indicators": ind, "matrix": matrix, "inconsistency": inconsistency, "leading": best})


def key_assumptions(val: ValuationResult, ctx: CompanyContext) -> TechniqueOutput:
    base = next((s for s in val.scenarios if s.name == "base"), None)
    m = ctx.fundamentals.metrics if ctx.fundamentals else {}
    rows = []
    if base:
        a = base.assumptions
        g_hist = m.get("revenue_growth_yoy")
        rows.append({"assumption": f"Revenue grows {a['revenue_growth']:.0%} next 12m",
                     "basis": f"75% of trailing growth {g_hist:.0%}" if g_hist is not None else "default 5% (no history)",
                     "status": "supported" if g_hist is not None and g_hist >= a["revenue_growth"] else "unsupported"})
        rows.append({"assumption": f"Exit EV/revenue {a['ev_revenue']:.2f}x",
                     "basis": "geometric mean of current and peer median" if val.peer_ev_revenue_median else "own current multiple",
                     "status": "supported" if val.peer_ev_revenue_median else "weak (no peer set)"})
        rows.append({"assumption": f"Dilution {a['dilution']:.0%}", "basis": "trailing share-count change",
                     "status": "supported" if m.get("dilution_yoy") is not None else "unsupported"})
        rows.append({"assumption": "No covenant breach / financing shock", "basis": "liquidity metrics",
                     "status": "contradicted" if (m.get("cash_runway_months") or 99) < 12 else "supported"})
    return TechniqueOutput(technique="Key Assumptions Check", summary=f"{sum(r['status'] == 'supported' for r in rows)}/{len(rows)} base-case assumptions supported by evidence",
                           details={"assumptions": rows}, applied=bool(rows))


def indicators_signposts(ctx: CompanyContext, val: ValuationResult) -> TechniqueOutput:
    m = ctx.fundamentals.metrics if ctx.fundamentals else {}
    signs = []
    if m.get("backlog") is not None:
        signs.append({"indicator": "Backlog (RPO) YoY", "current": m.get("backlog_growth_yoy"), "bullish_if": ">= +20%", "bearish_if": "< 0%"})
    signs.append({"indicator": "Quarterly revenue YoY", "current": m.get("revenue_q_yoy"), "bullish_if": "accelerates", "bearish_if": "< +10%"})
    signs.append({"indicator": "Gross margin", "current": m.get("gross_margin"), "bullish_if": "+2pts YoY", "bearish_if": "-3pts YoY"})
    signs.append({"indicator": "Share count", "current": m.get("dilution_yoy"), "bullish_if": "<= +2%", "bearish_if": "> +10% or new ATM"})
    signs.append({"indicator": "Federal awards (USAspending)", "current": len(ctx.contracts), "bullish_if": "new award > 5% revenue", "bearish_if": "none for 2 quarters"})
    if val.growth_required_to_double_at_current_multiple is not None:
        signs.append({"indicator": "Revenue needed to double at current multiple", "current": val.revenue_required_to_double_at_current_multiple,
                      "bullish_if": "guidance implies this level", "bearish_if": "guidance below TTM"})
    if ctx.findings:
        for c in ctx.findings.upcoming_catalysts[:5]:
            signs.append({"indicator": f"Catalyst: {c.event}", "current": str(c.expected_date), "bullish_if": "occurs on time", "bearish_if": "slips/cancelled"})
    for ch in ctx.policy_chains[:3]:
        signs.append({"indicator": f"Policy stage: {ch.policy[:60]}", "current": ch.stage, "bullish_if": "moves to enforcement", "bearish_if": "reversed/expired"})
    return TechniqueOutput(technique="Indicators and Signposts", summary=f"{len(signs)} leading indicators tracked", details={"signposts": signs})


def red_team(ctx: CompanyContext, results: list[AssignmentResult], vetoes: list[RiskVeto], val: ValuationResult) -> TechniqueOutput:
    strongest_no = sorted([r for r in results if r.vote == Vote.NO], key=lambda r: r.confidence, reverse=True)[:8]
    negatives = [e for e, r in ctx.finding_ev if r["sentiment"] == "negative" and r["evidence_type"] == "verified"]
    bear = next((s for s in val.scenarios if s.name == "bear"), None)
    high = [r for r in (ctx.findings.key_risks if ctx.findings else []) if r.severity in ("high", "critical")]
    failures = []
    if bear and bear.upside_pct is not None and bear.upside_pct < -0.6:
        failures.append(f"bear case {bear.upside_pct:.0%}")
    if val.monte_carlo and val.monte_carlo.p_loss_50 is not None and val.monte_carlo.p_loss_50 > 0.3:
        failures.append(f"model-implied P(-50%) {val.monte_carlo.p_loss_50:.0%}")
    if len(high) >= 2:
        failures.append(f"{len(high)} high/critical research risks")
    if any(v.severity == "critical" for v in vetoes):
        failures.append("critical veto present")
    survives = not failures
    return TechniqueOutput(technique="Red Team Analysis", summary=(
        "Thesis survives red-team challenge" if survives else "Red team defeats thesis: " + "; ".join(failures)),
        details={"survives": survives, "failures": failures,
                 "strongest_counter_votes": [{"id": r.assignment_id, "q": r.question, "finding": r.finding} for r in strongest_no],
                 "verified_negatives": [{"claim": e.claim, "url": e.source_url, "date": str(e.published_date)} for e in negatives[:8]],
                 "high_risks": [r.risk for r in high]})


def devils_advocacy(results: list[AssignmentResult], ctx: CompanyContext) -> TechniqueOutput:
    by_group: dict[str, list[AssignmentResult]] = {}
    for r in results:
        if r.vote == Vote.YES:
            by_group.setdefault(r.group, []).append(r)
    if not by_group:
        return TechniqueOutput(technique="Devil's Advocacy", summary="No YES votes to challenge", applied=False)
    g = max(by_group, key=lambda k: len(by_group[k]))
    weak = []
    for r in by_group[g]:
        evs = [ctx.evidence[i] for i in r.supporting_evidence if i in ctx.evidence]
        if len(evs) <= 1 or all(e.evidence_type.value != "verified" for e in evs) or r.dependent_on:
            weak.append({"id": r.assignment_id, "question": r.question, "why_weak": "single/unverified/duplicate evidence"})
    return TechniqueOutput(technique="Devil's Advocacy", summary=f"Challenged strongest group '{g}' ({len(by_group[g])} YES): {len(weak)} rest on thin evidence",
                           details={"group": g, "weak_votes": weak})


def premortem(ctx: CompanyContext, results: list[AssignmentResult], vetoes: list[RiskVeto], val: ValuationResult) -> TechniqueOutput:
    causes = [v.description for v in vetoes]
    causes += [r.finding for r in results if r.vote == Vote.NO and r.group in ("risk_forensic", "company_financial")][:6]
    if ctx.findings:
        causes += [r.risk for r in ctx.findings.key_risks[:5]]
    bear = next((s for s in val.scenarios if s.name == "bear"), None)
    if bear:
        causes.append(f"Bear-case mechanics: growth {bear.assumptions.get('revenue_growth', 0):.0%}, multiple {bear.assumptions.get('ev_revenue', 0):.2f}x, dilution {bear.assumptions.get('dilution', 0):.0%}")
    return TechniqueOutput(technique="Premortem Analysis", summary="Assume the position lost 50% in 12 months; most plausible causes listed",
                           details={"failure_causes": list(dict.fromkeys(causes))[:12]})


def scenario_summary(val: ValuationResult) -> TechniqueOutput:
    rows = [{"scenario": s.name, "implied_price": s.implied_price, "upside": s.upside_pct, "assumptions": s.assumptions,
             "probability": s.probability, "probability_basis": s.probability_basis} for s in val.scenarios]
    return TechniqueOutput(technique="Scenario Analysis", summary=(
        f"bull {'meets' if val.bull_meets_double else 'does not meet'} +100% target" if val.scenarios else "not run (inputs missing)"),
        details={"scenarios": rows, "target_price_double": val.price_to_double}, applied=bool(rows))


def cross_impact(results: list[AssignmentResult]) -> TechniqueOutput:
    drivers = {
        "policy_tailwind": [1, 2, 3, 6, 14, 64, 71, 75],
        "demand_growth": [16, 17, 18, 29, 35],
        "financing_risk": [25, 27, 81, 85],
        "competition": [33, 42],
        "valuation_room": [46, 47, 50, 56],
    }
    state = {}
    for d, ids in drivers.items():
        votes = [r.vote for r in results if r.assignment_id in ids]
        y, n = votes.count(Vote.YES), votes.count(Vote.NO)
        state[d] = "favorable" if y > n else "adverse" if n > y else "unknown"
    effects = {
        "policy_tailwind": {"demand_growth": "+", "valuation_room": "+"},
        "demand_growth": {"financing_risk": "-", "valuation_room": "+"},
        "financing_risk": {"valuation_room": "-", "demand_growth": "-"},
        "competition": {"demand_growth": "-", "valuation_room": "-"},
        "valuation_room": {},
    }
    return TechniqueOutput(technique="Cross-Impact Analysis", summary=", ".join(f"{k}={v}" for k, v in state.items()),
                           details={"driver_states": state, "impact_matrix": effects})


def bayesian(calibration_path: Path, results: list[AssignmentResult]) -> TechniqueOutput:
    if not calibration_path.exists():
        return TechniqueOutput(technique="Bayesian Update", applied=False, summary=(
            "Not applied: no calibrated base rate or likelihood ratios on file. Supply data/calibration/base_rates.json "
            "from a point-in-time backtest to enable."), details={})
    cal = json.loads(calibration_path.read_text())
    prior = cal["prior_p_double"]
    odds = prior / (1 - prior)
    used = []
    for r in results:
        lr = cal.get("likelihood_ratios", {}).get(str(r.assignment_id))
        if lr and r.vote != Vote.UNKNOWN:
            ratio = lr["yes"] if r.vote == Vote.YES else lr["no"]
            odds *= ratio
            used.append({"id": r.assignment_id, "lr": ratio})
    post = odds / (1 + odds)
    return TechniqueOutput(technique="Bayesian Update", summary=f"Calibrated prior {prior:.1%} -> posterior {post:.1%} using {len(used)} LRs",
                           details={"prior": prior, "posterior": post, "used": used, "calibration_source": cal.get("source")})


def sensitivity_summary(val: ValuationResult) -> TechniqueOutput:
    mc = val.monte_carlo
    return TechniqueOutput(technique="Sensitivity & Monte Carlo", applied=mc is not None, summary=(
        f"MC (n={mc.simulations}, seed={mc.seed}): P(>=2x)={mc.p_double:.1%}, P(<=0.5x)={mc.p_loss_50:.1%}, "
        f"median ${mc.median_price:,.2f} — {mc.label}" if mc else "not run"),
        details={"grid": [c.model_dump() for c in val.sensitivity], "monte_carlo": mc.model_dump() if mc else None})


def run_all(ctx, results, vetoes, val, calibration_path: Path) -> list[TechniqueOutput]:
    return [ach(ctx, val), key_assumptions(val, ctx), indicators_signposts(ctx, val), red_team(ctx, results, vetoes, val),
            devils_advocacy(results, ctx), premortem(ctx, results, vetoes, val), scenario_summary(val),
            cross_impact(results), bayesian(calibration_path, results), sensitivity_summary(val)]


__all__ = ["run_all", "Sentiment"]
