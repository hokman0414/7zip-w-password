"""Structured-analytic feedback across daily runs.

Compares today's ACH hypothesis, red-team result, and monthly-return correlations with the previous
snapshot. The notes are the loop the next run reads. This module never places or proposes orders.
"""
from __future__ import annotations

import json
from datetime import datetime

from .config import Settings

PAIR_THRESHOLD = 0.75


def _technique(report, name: str):
    for t in getattr(report, "techniques", []) or []:
        if getattr(t, "technique", "") == name:
            return t
    return None


def _snapshot(reports, risk: dict | None) -> dict:
    held = {h.symbol for h in (risk or {}).get("holdings", []) if h.value >= 1}
    hypotheses, red = {}, {}
    for r in reports:
        if held and r.ticker not in held:
            continue
        ach = _technique(r, "Analysis of Competing Hypotheses")
        if ach and ach.details.get("leading"):
            hypotheses[r.ticker] = ach.details["leading"]
        team = _technique(r, "Red Team Analysis")
        if team and "survives" in team.details:
            red[r.ticker] = bool(team.details["survives"])
    return {"hypotheses": hypotheses, "red_team_survives": red,
            "pairs": list((risk or {}).get("correlation_pairs") or [])}


def _pair_map(pairs: list[dict]) -> dict[tuple[str, str], float]:
    return {tuple(sorted((p["a"], p["b"]))): float(p["corr"]) for p in pairs}


def _notes(prior: dict, current: dict, risk: dict | None) -> list[str]:
    if not prior:
        return ["First SAT feedback snapshot. The next run compares hypotheses and correlations with this one.",
                "Correlation and SAT notes do not create an order. A sell still has to be a risk-cap trim in the plan."]
    weights = {h.symbol: h.weight for h in (risk or {}).get("holdings", [])}
    notes = []
    old_h, new_h = prior.get("hypotheses") or {}, current["hypotheses"]
    old_r, new_r = prior.get("red_team_survives") or {}, current["red_team_survives"]
    for ticker in sorted(set(old_h) | set(new_h)):
        before, after = old_h.get(ticker), new_h.get(ticker)
        if before and after and before != after:
            notes.append(f"{ticker} ACH leading hypothesis {before} -> {after}")
        if ticker in old_r and ticker in new_r and old_r[ticker] and not new_r[ticker]:
            notes.append(f"{ticker} red team now defeats the thesis")
        elif ticker in old_r and ticker in new_r and not old_r[ticker] and new_r[ticker]:
            notes.append(f"{ticker} red team no longer defeats the thesis")
    old_p, new_p = _pair_map(prior.get("pairs") or []), _pair_map(current["pairs"])
    for key in sorted(set(old_p) | set(new_p)):
        before, after = old_p.get(key), new_p.get(key)
        label = f"{key[0]}-{key[1]}"
        weight = weights.get(key[0], 0) + weights.get(key[1], 0)
        if before is None and after is not None and after > PAIR_THRESHOLD:
            notes.append(f"{label} monthly correlation {after:.2f} is above 0.75 (combined weight {weight:.1%})")
        elif after is None and before is not None and before > PAIR_THRESHOLD:
            notes.append(f"{label} left the correlation set (was {before:.2f})")
        elif before is not None and after is not None and (before > PAIR_THRESHOLD) != (after > PAIR_THRESHOLD):
            side = "rose through" if after > PAIR_THRESHOLD else "fell through"
            notes.append(f"{label} correlation {before:.2f} -> {after:.2f}, {side} 0.75")
    if not notes:
        notes.append("No SAT hypothesis change and no correlation crossing 0.75 since the prior run.")
    notes.append("Correlation and SAT notes do not create an order. A sell still has to be a risk-cap trim in the plan.")
    return notes


def update_feedback(settings: Settings, reports, risk: dict | None, now: datetime) -> dict:
    path = settings.data_dir / "state" / "sat_feedback.json"
    prior = json.loads(path.read_text()) if path.exists() else {}
    current = _snapshot(reports, risk)
    notes = _notes(prior, current, risk)
    payload = {"as_of": now.isoformat(), "prior_as_of": prior.get("as_of"), **current, "notes": notes}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return payload
