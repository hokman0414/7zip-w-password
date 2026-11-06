from __future__ import annotations

from silent_stocks.models import RiskVeto, Status
from silent_stocks.voting import decide_status, risk_vetoes, tally

from .conftest import NOW, ev, make_ctx, result
from silent_stocks.models import Vote


def codes(ctx):
    return {v.code: v.severity for v in risk_vetoes(ctx, NOW, 96)}


def test_healthy_company_has_no_critical_veto(healthy_metrics):
    assert "critical" not in codes(make_ctx(healthy_metrics)).values()


def test_cash_runway_under_12_months(healthy_metrics):
    assert codes(make_ctx(healthy_metrics | {"cash_runway_months": 7.4}))["CASH_RUNWAY"] == "critical"


def test_severe_dilution(healthy_metrics):
    assert codes(make_ctx(healthy_metrics | {"dilution_yoy": 0.31}))["SEVERE_DILUTION"] == "critical"
    assert "SEVERE_DILUTION" not in codes(make_ctx(healthy_metrics | {"dilution_yoy": 0.29}))


def test_negative_equity(healthy_metrics):
    assert codes(make_ctx(healthy_metrics | {"stockholders_equity": -1.0}))["NEGATIVE_EQUITY"] == "critical"


def test_going_concern_from_filing_search(healthy_metrics):
    s = {"substantial doubt": {"ok": True, "hits": [{"form": "10-Q"}], "hit_evidence": ["x"]}}
    assert codes(make_ctx(healthy_metrics, searches=s))["GOING_CONCERN"] == "critical"


def test_listing_and_sub_dollar(healthy_metrics):
    c = codes(make_ctx(healthy_metrics, price=0.6, listing="Noncompliant"))
    assert c["LISTING_NONCOMPLIANT"] == "critical" and c["SUB_DOLLAR"] == "critical"


def test_material_weakness_is_warning_only(healthy_metrics):
    s = {"material weakness": {"ok": True, "hits": [{}], "hit_evidence": []}}
    assert codes(make_ctx(healthy_metrics, searches=s))["MATERIAL_WEAKNESS"] == "warning"


def test_missing_fundamentals_is_critical():
    assert codes(make_ctx(None))["MISSING_FUNDAMENTALS"] == "critical"


def test_critical_veto_overrides_passing_vote():
    t = tally([result(i, Vote.YES, [ev(i).id]) for i in range(1, 101)])
    assert t.passes_gate
    v = [RiskVeto(code="CASH_RUNWAY", description="x", severity="critical")]
    assert decide_status(t, v, True, True, False, True)[0] == Status.DISQUALIFIED


def test_warning_does_not_disqualify():
    t = tally([result(i, Vote.YES, [ev(i).id]) for i in range(1, 101)])
    v = [RiskVeto(code="MATERIAL_WEAKNESS", description="x", severity="warning")]
    assert decide_status(t, v, True, True, False, True)[0] == Status.QUALIFIED


class TestStaleData:
    def test_old_price_is_stale(self, healthy_metrics):
        assert codes(make_ctx(healthy_metrics, price_age_h=200))["STALE_MARKET_DATA"] == "critical"

    def test_weekend_price_is_not_stale(self, healthy_metrics):
        assert "STALE_MARKET_DATA" not in codes(make_ctx(healthy_metrics, price_age_h=70))

    def test_stale_status_takes_precedence(self, healthy_metrics):
        ctx = make_ctx(healthy_metrics, price_age_h=200)
        v = risk_vetoes(ctx, NOW, 96)
        t = tally([result(i, Vote.YES, [ev(i).id]) for i in range(1, 101)])
        assert decide_status(t, v, True, True, False, True)[0] == Status.STALE_DATA

    def test_no_price_is_critical(self, healthy_metrics):
        assert codes(make_ctx(healthy_metrics, price=None))["NO_MARKET_DATA"] == "critical"
