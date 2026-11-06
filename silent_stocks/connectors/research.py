"""Loads research-agent findings (web-sourced, per ticker) and international policy events, validated by Pydantic."""
from __future__ import annotations

import json
import logging
import datetime as _dt
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

log = logging.getLogger(__name__)


def _lenient_date(v):
    if v in (None, "", "null"):
        return None
    if isinstance(v, (date, datetime)):
        return v if isinstance(v, date) else v.date()
    s = str(v)[:10]
    try:
        return date.fromisoformat(s)
    except ValueError:
        try:
            return date.fromisoformat(s[:7] + "-01")
        except ValueError:
            return None


class Finding(BaseModel):
    dimension: str
    topic: str = "other"
    claim: str
    evidence_type: Literal["verified", "analyst_judgment", "unsupported_hypothesis"]
    sentiment: Literal["positive", "negative", "neutral"]
    source_url: str
    source_title: str = ""
    published_date: date | None = None

    _d = field_validator("published_date", mode="before")(_lenient_date)


class AgentCatalyst(BaseModel):
    event: str
    expected_date: date | None = None
    date_confidence: str = "unknown"
    source_url: str = ""

    _d = field_validator("expected_date", mode="before")(_lenient_date)


class AgentPolicyLink(BaseModel):
    country: str
    policy: str
    stage: str
    industry: str = ""
    bottleneck: str = ""
    revenue_mechanism: str = ""
    evidence_of_company_revenue: bool = False
    source_url: str
    published_date: date | None = None

    _d = field_validator("published_date", mode="before")(_lenient_date)


class AgentRisk(BaseModel):
    risk: str
    severity: Literal["low", "medium", "high", "critical"]
    source_url: str = ""
    published_date: date | None = None

    _d = field_validator("published_date", mode="before")(_lenient_date)


class DilutionEvent(BaseModel):
    description: str
    date: _dt.date | None = None
    source_url: str = ""

    _d = field_validator("date", mode="before")(_lenient_date)


class AgentFindings(BaseModel):
    ticker: str
    company: str = ""
    researched_at: datetime
    agent_id: str
    findings: list[Finding] = Field(default_factory=list)
    upcoming_catalysts: list[AgentCatalyst] = Field(default_factory=list)
    policy_links: list[AgentPolicyLink] = Field(default_factory=list)
    key_risks: list[AgentRisk] = Field(default_factory=list)
    dilution_events_last_12m: list[DilutionEvent] = Field(default_factory=list)
    going_concern_warning: bool | None = None
    notes: str = ""


class PolicyEvent(BaseModel):
    id: str
    country: str
    policy: str
    stage: str
    event_date: date | None = None
    expiration_date: date | None = None
    industries: list[str] = Field(default_factory=list)
    bottlenecks: list[str] = Field(default_factory=list)
    direction: str = "mixed"
    summary: str = ""
    source_url: str
    source_title: str = ""

    _d = field_validator("event_date", "expiration_date", mode="before")(_lenient_date)


def load_findings(findings_dir: Path, as_of: datetime | None = None) -> dict[str, AgentFindings]:
    """Point-in-time: findings researched after `as_of`, or individual claims published after it, are excluded."""
    out: dict[str, AgentFindings] = {}
    if not findings_dir.exists():
        return out
    for path in sorted(findings_dir.glob("*.json")):
        try:
            doc = AgentFindings.model_validate(json.loads(path.read_text()))
        except (ValidationError, json.JSONDecodeError) as exc:
            log.error("invalid findings file %s: %s", path, exc)
            continue
        if as_of is not None:
            if doc.researched_at > as_of:
                continue
            cutoff = as_of.date()
            doc.findings = [f for f in doc.findings if f.published_date is None or f.published_date <= cutoff]
            doc.policy_links = [p for p in doc.policy_links if p.published_date is None or p.published_date <= cutoff]
            doc.key_risks = [r for r in doc.key_risks if r.published_date is None or r.published_date <= cutoff]
        out[doc.ticker.upper()] = doc
    return out


def load_policy_events(path: Path, as_of: date | None = None) -> list[PolicyEvent]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    events = []
    for item in raw.get("events", []):
        try:
            ev = PolicyEvent.model_validate(item)
        except ValidationError as exc:
            log.error("invalid policy event %s: %s", item.get("id"), exc)
            continue
        if as_of and ev.event_date and ev.event_date > as_of:
            continue
        events.append(ev)
    return events
