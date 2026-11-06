from __future__ import annotations

import pytest

from silent_stocks.models import AssignmentResult, Status, Vote
from silent_stocks.voting import decide_status, tally

from .conftest import ev, result


def _results(yes: int, no: int = 0, unknown: int = 0, distinct: bool = True) -> list[AssignmentResult]:
    out, i = [], 1
    for k in range(yes):
        out.append(result(i, Vote.YES, [ev(k if distinct else 0).id]))
        i += 1
    for _ in range(no):
        out.append(result(i, Vote.NO))
        i += 1
    for _ in range(unknown):
        out.append(result(i, Vote.UNKNOWN))
        i += 1
    return out


class TestScoreThresholds:
    def test_80_independent_yes_passes(self):
        t = tally(_results(80, 20))
        assert t.passes_gate and t.independent_yes == 80

    def test_79_yes_fails(self):
        t = tally(_results(79, 21))
        assert not t.passes_gate
        assert "79 independent YES < 80" in t.gate_reason

    def test_disclaimer_rejects_probability_reading(self):
        assert "NOT an 80% probability" in tally(_results(80, 20)).disclaimer


class TestMissingInformation:
    def test_unknown_never_counts_as_yes(self):
        t = tally(_results(70, 0, 30))
        assert t.yes == 70 and t.unknown == 30 and not t.passes_gate

    def test_gate_requires_all_100_completed(self):
        t = tally(_results(85))
        assert t.completed == 85 and not t.passes_gate
        assert "only 85/100" in t.gate_reason

    def test_yes_without_evidence_is_rejected(self):
        with pytest.raises(ValueError):
            result(1, Vote.YES, [])


class TestDuplicateEvidence:
    def test_identical_evidence_collapses(self):
        t = tally(_results(90, 10, distinct=False))
        assert t.yes == 90 and t.independent_yes == 1 and t.dependent_yes == 89 and not t.passes_gate

    def test_dependent_vote_records_origin(self):
        rs = _results(3, 97, distinct=False)
        tally(rs)
        assert rs[0].dependent_on is None and rs[1].dependent_on == rs[0].assignment_id

    def test_evidence_id_is_content_fingerprint(self):
        assert ev(5).id == ev(5).id != ev(6).id


class TestStatus:
    def _t(self, n):
        return tally(_results(n, 100 - n))

    def test_qualified_needs_gate_double_and_red_team(self):
        assert decide_status(self._t(85), [], True, True, False, True)[0] == Status.QUALIFIED
        assert decide_status(self._t(85), [], False, True, False, True)[0] == Status.UNDER_REVIEW
        assert decide_status(self._t(85), [], True, True, False, False)[0] == Status.UNDER_REVIEW

    def test_no_research_is_discovery(self):
        assert decide_status(self._t(85), [], True, False, False, True)[0] == Status.DISCOVERY

    def test_stale_research_marks_stale(self):
        assert decide_status(self._t(85), [], True, True, True, True)[0] == Status.STALE_DATA
