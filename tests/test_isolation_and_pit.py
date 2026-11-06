from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from silent_stocks.assignments import REGISTRY
from silent_stocks.connectors.research import load_findings
from silent_stocks.context import SliceAccessError, SliceView
from silent_stocks.financials import compute_fundamentals
from silent_stocks.models import Vote
from silent_stocks.voting import run_assignments

from .conftest import make_ctx


def test_exactly_100_assignments_with_group_counts():
    assert len(REGISTRY) == 100
    assert sorted(s.id for s, _ in REGISTRY) == list(range(1, 101))
    counts = {}
    for s, _ in REGISTRY:
        counts[s.group] = counts.get(s.group, 0) + 1
    assert counts == {"macro_policy": 15, "company_financial": 15, "technology_competitive": 15, "valuation_mispricing": 15,
                      "military_geopolitical": 10, "supply_chain_industrial": 10, "risk_forensic": 10, "catalyst_alternative": 10}


def test_slice_view_blocks_undeclared_access():
    v = SliceView(make_ctx({"revenue_ttm": 1.0}), ("market",))
    with pytest.raises(SliceAccessError):
        v.fin("revenue_ttm")


def test_empty_context_produces_no_unsupported_yes():
    results = run_assignments(make_ctx(None, price=None))
    assert len(results) == 100
    assert all(r.supporting_evidence for r in results if r.vote == Vote.YES)
    assert sum(r.vote == Vote.UNKNOWN for r in results) >= 60
    assert {r.executor for r in results} == {"rule-based"}


def _fact(start, end, val, filed):
    return {"start": start, "end": end, "val": val, "filed": filed, "form": "10-Q", "accn": "a"}


def test_xbrl_point_in_time_ignores_later_filings():
    rows = [_fact("2025-01-01", "2025-03-31", 10, "2025-05-01"), _fact("2025-04-01", "2025-06-30", 11, "2025-08-01"),
            _fact("2025-07-01", "2025-09-30", 12, "2025-11-01"), _fact("2025-10-01", "2025-12-31", 13, "2026-02-20"),
            _fact("2026-01-01", "2026-03-31", 14, "2026-05-01"), _fact("2026-04-01", "2026-06-30", 15, "2026-08-01"),
            _fact("2026-07-01", "2026-09-30", 99, "2026-11-01")]
    facts = {"entityName": "X", "facts": {"us-gaap": {"Revenues": {"units": {"USD": rows}}}}}
    before = compute_fundamentals(1, facts, date(2026, 10, 15))
    after = compute_fundamentals(1, facts, date(2026, 11, 2))
    assert before.metrics["revenue_ttm"] == 12 + 13 + 14 + 15
    assert after.metrics["revenue_ttm"] == 13 + 14 + 15 + 99


def test_findings_point_in_time(tmp_path):
    doc = {"ticker": "T", "researched_at": "2026-11-06T12:00:00Z", "agent_id": "a", "findings": [
        {"dimension": "economic", "claim": "old", "evidence_type": "verified", "sentiment": "positive", "source_url": "https://a", "published_date": "2026-10-01"},
        {"dimension": "economic", "claim": "future", "evidence_type": "verified", "sentiment": "positive", "source_url": "https://b", "published_date": "2026-12-01"}]}
    (tmp_path / "T.json").write_text(json.dumps(doc))
    assert load_findings(tmp_path, datetime(2026, 11, 1, tzinfo=timezone.utc)) == {}
    got = load_findings(tmp_path, datetime(2026, 11, 7, tzinfo=timezone.utc))
    assert [f.claim for f in got["T"].findings] == ["old"]
