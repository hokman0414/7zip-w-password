"""Assignment execution, evidence-dependency detection, vote tally and mandatory risk vetoes."""
from __future__ import annotations

import logging
import time
from datetime import datetime

from .assignments import REGISTRY, Outcome
from .context import CompanyContext, SliceAccessError, SliceView
from .models import AssignmentResult, RiskVeto, Status, Vote, VoteTally

log = logging.getLogger(__name__)


def _impact(vote: Vote, responsibility: str) -> str:
    verb = {"YES": "Supports", "NO": "Weakens", "UNKNOWN": "Does not update"}[vote.value]
    return f"{verb} the 12-month thesis on: {responsibility.lower()}"


def run_assignments(ctx: CompanyContext, executor=None) -> list[AssignmentResult]:
    """Execute all 100 assignments. `executor` (optional) is an LLM adapter with .evaluate(spec, view, outcome)."""
    results = []
    for spec, fn in REGISTRY:
        view = SliceView(ctx, spec.inputs)
        t0 = time.perf_counter()
        label = "rule-based"
        try:
            out: Outcome = fn(view)
            if executor is not None:
                out, label = executor.evaluate(spec, view, out)
        except SliceAccessError as exc:
            log.error("assignment %s violated isolation: %s", spec.id, exc)
            out = Outcome(Vote.UNKNOWN, 0.0, f"isolation violation: {exc}", [], [])
        except Exception as exc:  # noqa: BLE001 - one failing evaluator abstains instead of aborting the run
            log.exception("assignment %s failed", spec.id)
            out = Outcome(Vote.UNKNOWN, 0.0, f"evaluator error: {type(exc).__name__}: {exc}", [], [])
        support = [i for i in dict.fromkeys(out.support) if i]
        contra = [i for i in dict.fromkeys(out.contra) if i]
        evs = [ctx.evidence[i] for i in support + contra if i in ctx.evidence]
        payload = dict(
            assignment_id=spec.id, group=spec.group, dimension=spec.dimension, question=spec.question,
            vote=out.vote, confidence=out.confidence, finding=out.finding, supporting_evidence=support,
            contradicting_evidence=contra, source_urls=sorted({e.source_url for e in evs}),
            source_dates=sorted({str(e.published_date) for e in evs if e.published_date}),
            falsification_condition=spec.falsification, thesis_impact=_impact(out.vote, spec.responsibility),
            executor=label, inputs_used=list(spec.inputs), input_fingerprint=view.fingerprint(),
            duration_ms=round((time.perf_counter() - t0) * 1000, 3),
        )
        try:
            results.append(AssignmentResult(**payload))
        except ValueError as exc:
            payload.update(vote=Vote.UNKNOWN, confidence=0.0, finding=f"{out.finding} [downgraded: {exc.errors()[0]['msg'] if hasattr(exc, 'errors') else exc}]",
                           thesis_impact=_impact(Vote.UNKNOWN, spec.responsibility))
            results.append(AssignmentResult(**payload))
    return results


def tally(results: list[AssignmentResult], threshold: int = 80, total: int = 100) -> VoteTally:
    yes = [r for r in results if r.vote == Vote.YES]
    no = sum(r.vote == Vote.NO for r in results)
    unk = sum(r.vote == Vote.UNKNOWN for r in results)
    seen: dict[frozenset, int] = {}
    dependent = 0
    for r in yes:
        key = frozenset(r.supporting_evidence)
        if key in seen:
            r.dependent_on = seen[key]
            dependent += 1
        else:
            seen[key] = r.assignment_id
    independent = len(yes) - dependent
    completed = len(results)
    if completed != total:
        passes, reason = False, f"only {completed}/{total} assignments completed; gate requires exactly {total}"
    elif independent >= threshold:
        passes, reason = True, f"{independent} independent YES >= {threshold}"
    else:
        passes, reason = False, f"{independent} independent YES < {threshold} ({len(yes)} raw YES, {dependent} collapsed as duplicate evidence)"
    return VoteTally(yes=len(yes), no=no, unknown=unk, completed=completed, independent_yes=independent,
                     dependent_yes=dependent, threshold=threshold, passes_gate=passes, gate_reason=reason)


def risk_vetoes(ctx: CompanyContext, now: datetime, stale_hours: float) -> list[RiskVeto]:
    v: list[RiskVeto] = []
    f = ctx.fundamentals
    md = ctx.market
    m = f.metrics if f else {}

    def ev_ids(*keys):
        return [f.evidence[k].id for k in keys if f and k in f.evidence]

    if md is None or md.price is None:
        v.append(RiskVeto(code="NO_MARKET_DATA", description="No verified market price", severity="critical"))
    else:
        age = md.age_hours(now)
        if age is None or age > stale_hours:
            v.append(RiskVeto(code="STALE_MARKET_DATA", description=f"Market data age {age:.0f}h exceeds {stale_hours:.0f}h" if age is not None else "Market data has no timestamp", severity="critical"))
        if (md.listing_status or "").lower() == "noncompliant":
            v.append(RiskVeto(code="LISTING_NONCOMPLIANT", description="Exchange listing noncompliance reported by broker data", severity="critical"))
        if md.price < 1.0:
            v.append(RiskVeto(code="SUB_DOLLAR", description=f"Share price ${md.price} below $1 (delisting/reverse-split risk)", severity="critical"))
        if md.return_12m is not None and md.return_12m > 1.5:
            v.append(RiskVeto(code="ALREADY_MOVED", description=f"Price up {md.return_12m:.0%} in 12 months; original opportunity may be captured", severity="warning"))
    if f is None or m.get("revenue_ttm") is None:
        v.append(RiskVeto(code="MISSING_FUNDAMENTALS", description="No point-in-time SEC revenue; thesis cannot be evaluated", severity="critical"))
    gc = ctx.filing_searches.get("substantial doubt")
    if (gc and gc.get("hits")) or (ctx.findings and ctx.findings.going_concern_warning):
        v.append(RiskVeto(code="GOING_CONCERN", description="Going-concern doubt in filings or research", severity="critical",
                          evidence_ids=(gc or {}).get("hit_evidence", [])))
    runway = m.get("cash_runway_months")
    if runway is not None and runway < 12:
        v.append(RiskVeto(code="CASH_RUNWAY", description=f"Cash runway ~{runway:.0f} months (<12) at TTM burn", severity="critical", evidence_ids=ev_ids("cash_runway_months")))
    dil = m.get("dilution_yoy")
    if dil is not None and dil > 0.30:
        v.append(RiskVeto(code="SEVERE_DILUTION", description=f"Share count up {dil:.0%} in ~12 months", severity="critical", evidence_ids=ev_ids("dilution_yoy")))
    eq = m.get("stockholders_equity")
    if eq is not None and eq < 0:
        v.append(RiskVeto(code="NEGATIVE_EQUITY", description="Stockholders' equity is negative", severity="critical", evidence_ids=ev_ids("stockholders_equity")))
    mw = ctx.filing_searches.get("material weakness")
    if mw and mw.get("hits"):
        v.append(RiskVeto(code="MATERIAL_WEAKNESS", description="Material weakness disclosed in last 12 months", severity="warning", evidence_ids=mw.get("hit_evidence", [])))
    nr = ctx.filing_searches.get("non-reliance")
    if nr and nr.get("hits"):
        v.append(RiskVeto(code="RESTATEMENT", description="Non-reliance / restatement notice in last 12 months", severity="critical", evidence_ids=nr.get("hit_evidence", [])))
    if ctx.findings:
        crit = [r for r in ctx.findings.key_risks if r.severity == "critical"]
        if crit:
            v.append(RiskVeto(code="CRITICAL_RESEARCH_RISK", description="; ".join(r.risk[:120] for r in crit[:3]), severity="critical"))
    return v


def decide_status(tally_: VoteTally, vetoes: list[RiskVeto], bull_meets_double: bool | None, has_research: bool,
                  research_stale: bool, red_team_survives: bool) -> tuple[Status, str]:
    codes = {x.code for x in vetoes if x.severity == "critical"}
    if "STALE_MARKET_DATA" in codes or research_stale:
        return Status.STALE_DATA, "market or research data is stale; refresh before relying on results"
    if codes:
        return Status.DISQUALIFIED, "critical risk veto: " + ", ".join(sorted(codes))
    if not has_research:
        return Status.DISCOVERY, "screened on filings/market data only; research assignments pending"
    if tally_.passes_gate and bull_meets_double and red_team_survives:
        return Status.QUALIFIED, "passed 80/100 independent-evidence gate, bull case >= 2x, survived red team"
    if tally_.passes_gate:
        why = "bull case below 2x" if not bull_meets_double else "red-team challenge not survived"
        return Status.UNDER_REVIEW, f"passed vote gate but {why}"
    if tally_.independent_yes >= 65:
        return Status.UNDER_REVIEW, f"approaching qualification ({tally_.independent_yes}/100 independent YES)"
    return Status.DISQUALIFIED, f"insufficient evidence for thesis ({tally_.independent_yes}/100 independent YES)"
