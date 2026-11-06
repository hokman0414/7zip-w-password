from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from silent_stocks.connectors.market import MarketData
from silent_stocks.context import CompanyContext
from silent_stocks.financials import Fundamentals
from silent_stocks.models import AssignmentResult, Evidence, EvidenceType, Vote

NOW = datetime(2026, 11, 6, 14, 0, tzinfo=timezone.utc)


def ev(i: int, **kw) -> Evidence:
    return Evidence(claim=f"claim {i}", source_url=f"https://example.com/{i}", evidence_type=EvidenceType.VERIFIED,
                    provider="test", **kw)


def result(i: int, vote: Vote, support: list[str] | None = None) -> AssignmentResult:
    return AssignmentResult(assignment_id=i, group="g", dimension="economic", question=f"q{i}", vote=vote, confidence=0.5,
                            finding="f", supporting_evidence=support or [], falsification_condition="x", thesis_impact="y",
                            executor="test", inputs_used=["financials"], input_fingerprint="fp")


def make_ctx(metrics: dict | None = None, price: float | None = 10.0, price_age_h: float = 2.0, listing: str | None = None,
             findings=None, searches: dict | None = None) -> CompanyContext:
    md = None
    if price is not None:
        md = MarketData(ticker="TEST", company="Test Co", price=price, price_time=NOW - timedelta(hours=price_age_h),
                        source="test", market_cap=1e9, shares_outstanding=1e8, listing_status=listing,
                        price_12m_ago=price / 1.1)
    fx = None
    if metrics is not None:
        fx = Fundamentals(cik=1, name="Test Co", as_of=NOW.date())
        fx.metrics.update(metrics)
    return CompanyContext(ticker="TEST", company="Test Co", as_of=NOW, market=md, fundamentals=fx, valuation=None,
                          findings=findings, policy_events=[], policy_chains=[], contracts=[], filings=[],
                          filing_searches=searches or {}, industries=set())


@pytest.fixture
def now():
    return NOW


@pytest.fixture
def healthy_metrics():
    return {"revenue_ttm": 100e6, "revenue_growth_yoy": 0.4, "cash_runway_months": None, "dilution_yoy": 0.02,
            "stockholders_equity": 50e6, "fcf_ttm": 5e6, "cash": 40e6, "debt": 0.0, "gross_margin": 0.4}


__all__ = ["ev", "result", "make_ctx", "NOW", "date"]
