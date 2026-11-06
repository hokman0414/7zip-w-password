"""Typed analytical outputs. Every analytical claim is a Pydantic model so outputs are validated, not free text."""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceType(StrEnum):
    VERIFIED = "verified"
    ANALYST_JUDGMENT = "analyst_judgment"
    UNSUPPORTED_HYPOTHESIS = "unsupported_hypothesis"
    STATISTICAL_FORECAST = "statistical_forecast"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Vote(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class Status(StrEnum):
    DISCOVERY = "DISCOVERY"
    UNDER_REVIEW = "UNDER REVIEW"
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    STALE_DATA = "STALE DATA"


class Evidence(BaseModel):
    """One piece of sourced evidence. `id` is a content fingerprint so identical evidence collapses."""

    id: str = ""
    ticker: str | None = None
    claim: str
    source_url: str
    source_title: str = ""
    published_date: date | None = None
    retrieved_at: datetime = Field(default_factory=utcnow)
    evidence_type: EvidenceType
    provider: str
    sentiment: Sentiment = Sentiment.NEUTRAL
    metric: str | None = None
    value: float | None = None
    dimension: str | None = None
    topic: str | None = None

    @model_validator(mode="after")
    def _fingerprint(self) -> "Evidence":
        if not self.id:
            basis = f"{self.source_url}|{self.metric or ''}|{self.claim.strip().lower()}"
            self.id = hashlib.sha1(basis.encode()).hexdigest()[:16]
        return self


class AssignmentSpec(BaseModel):
    id: int = Field(ge=1, le=100)
    group: str
    dimension: str
    question: str
    responsibility: str
    inputs: tuple[str, ...]
    falsification: str


class AssignmentResult(BaseModel):
    assignment_id: int
    group: str
    dimension: str
    question: str
    vote: Vote
    confidence: float = Field(ge=0.0, le=1.0)
    finding: str
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    source_dates: list[str] = Field(default_factory=list)
    falsification_condition: str
    thesis_impact: str
    executor: str
    inputs_used: list[str]
    input_fingerprint: str
    executed_at: datetime = Field(default_factory=utcnow)
    duration_ms: float = 0.0
    dependent_on: int | None = None

    @model_validator(mode="after")
    def _yes_requires_evidence(self) -> "AssignmentResult":
        if self.vote == Vote.YES and not self.supporting_evidence:
            raise ValueError("A YES vote must cite at least one supporting evidence id")
        return self


class RiskVeto(BaseModel):
    code: str
    description: str
    severity: Literal["warning", "critical"]
    evidence_ids: list[str] = Field(default_factory=list)


class VoteTally(BaseModel):
    yes: int
    no: int
    unknown: int
    completed: int
    independent_yes: int
    dependent_yes: int
    threshold: int
    passes_gate: bool
    gate_reason: str
    disclaimer: str = (
        "The vote count is a research evidence threshold. 80/100 is NOT an 80% probability of the stock doubling."
    )


class Scenario(BaseModel):
    name: Literal["bear", "base", "bull"]
    implied_price: float | None
    upside_pct: float | None
    assumptions: dict[str, Any]
    probability: float | None = None
    probability_basis: str = "not calibrated; no probability assigned"


class SensitivityCell(BaseModel):
    revenue_growth: float
    ev_sales_multiple: float
    implied_price: float | None


class MonteCarloResult(BaseModel):
    simulations: int
    seed: int
    p_double: float | None
    p_loss_50: float | None
    median_price: float | None
    p5_price: float | None
    p95_price: float | None
    inputs: dict[str, Any]
    label: str = "statistical_forecast: model-implied under stated input distributions; not a calibrated probability"


class ValuationResult(BaseModel):
    ticker: str
    price: float | None
    price_time: datetime | None
    market_cap: float | None
    shares_outstanding: float | None
    diluted_shares: float | None
    cash: float | None
    debt: float | None
    net_debt: float | None
    enterprise_value: float | None
    revenue_ttm: float | None
    revenue_growth_yoy: float | None
    gross_margin: float | None
    operating_margin: float | None
    ebitda_ttm: float | None
    fcf_ttm: float | None
    backlog: float | None
    backlog_growth_yoy: float | None
    ev_revenue: float | None
    ev_ebitda: float | None
    pe: float | None
    peer_ev_revenue_median: float | None
    peer_group: str | None
    dilution_yoy: float | None
    price_to_double: float | None
    revenue_required_to_double_at_current_multiple: float | None
    revenue_required_to_double_at_peer_multiple: float | None
    growth_required_to_double_at_current_multiple: float | None
    scenarios: list[Scenario]
    bull_meets_double: bool | None
    sensitivity: list[SensitivityCell]
    monte_carlo: MonteCarloResult | None
    volatility_annual: float | None
    return_12m: float | None
    notes: list[str] = Field(default_factory=list)


class DimensionAssessment(BaseModel):
    dimension: str
    assessment: Literal["supportive", "adverse", "mixed", "insufficient"]
    summary: str
    positive: int
    negative: int
    verified: int
    evidence_ids: list[str]
    regions: list[str] = Field(default_factory=list)


class Catalyst(BaseModel):
    event: str
    expected_date: date | None
    date_confidence: str
    source_url: str
    within_3_12_months: bool | None = None


class PolicyChain(BaseModel):
    country: str
    policy: str
    stage: str
    industry: str
    bottleneck: str
    company: str
    revenue_mechanism: str
    evidence_of_company_revenue: bool
    earnings_impact: str
    valuation_impact: str
    evidence_ids: list[str]
    source_urls: list[str]


class TechniqueOutput(BaseModel):
    technique: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    applied: bool = True


class CompanyReport(BaseModel):
    run_id: str
    as_of: datetime
    ticker: str
    company: str
    status: Status
    price: float | None
    price_source: str | None
    price_time: datetime | None
    market_cap: float | None
    industry: str | None
    country_exposure: list[str]
    discovery_score: float | None
    discovery_components: dict[str, Any]
    stemple: list[DimensionAssessment]
    tally: VoteTally
    assignments: list[AssignmentResult]
    vetoes: list[RiskVeto]
    catalysts: list[Catalyst]
    policy_chains: list[PolicyChain]
    valuation: ValuationResult
    techniques: list[TechniqueOutput]
    reasons_could_double: list[str]
    reasons_could_fail: list[str]
    leading_indicators: list[str]
    new_developments: list[str] = Field(default_factory=list)
    evidence: list[Evidence]
    data_gaps: list[str]
    disclaimer: str = (
        "Research output only. A qualifying score is a research threshold, not a recommendation or guarantee. "
        "No orders are placed by this system."
    )

    @field_validator("ticker")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper().strip()
