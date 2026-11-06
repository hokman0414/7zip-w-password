"""Per-company evidence context and isolated slice views handed to analytical assignments."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from .connectors.market import MarketData
from .connectors.research import AgentFindings, PolicyEvent
from .financials import Fundamentals
from .models import Evidence, EvidenceType, PolicyChain, Sentiment, ValuationResult

SLICES = ("financials", "market", "valuation", "findings", "policy", "contracts", "filings", "risks", "catalysts")


@dataclass
class CompanyContext:
    ticker: str
    company: str
    as_of: datetime
    market: MarketData | None
    fundamentals: Fundamentals | None
    valuation: ValuationResult | None
    findings: AgentFindings | None
    policy_events: list[PolicyEvent]
    policy_chains: list[PolicyChain]
    contracts: list[dict]
    filings: list[dict]
    filing_searches: dict[str, dict]
    industries: set[str]
    evidence: dict[str, Evidence] = field(default_factory=dict)
    finding_ev: list[tuple[Evidence, dict]] = field(default_factory=list)

    def add(self, ev: Evidence) -> Evidence:
        self.evidence.setdefault(ev.id, ev)
        return self.evidence[ev.id]


class SliceAccessError(PermissionError):
    pass


class SliceView:
    """Read-only accessor that exposes only the declared evidence slices."""

    def __init__(self, ctx: CompanyContext, inputs: tuple[str, ...]):
        unknown = [i for i in inputs if i not in SLICES]
        if unknown:
            raise ValueError(f"unknown slices {unknown}")
        self._ctx = ctx
        self._inputs = set(inputs)
        self.ticker = ctx.ticker
        self.as_of = ctx.as_of

    def _need(self, s: str):
        if s not in self._inputs:
            raise SliceAccessError(f"slice '{s}' not declared for this assignment")

    def fingerprint(self) -> str:
        payload = {}
        for s in sorted(self._inputs):
            payload[s] = sorted(e.id for e in self._slice_evidence(s))
        return hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    def _slice_evidence(self, s: str) -> list[Evidence]:
        c = self._ctx
        if s == "financials" and c.fundamentals:
            return list(c.fundamentals.evidence.values())
        if s == "findings":
            return [e for e, _ in c.finding_ev]
        if s == "policy":
            return [c.evidence[i] for ch in c.policy_chains for i in ch.evidence_ids if i in c.evidence]
        if s == "contracts":
            return [e for e in c.evidence.values() if e.provider == "usaspending"]
        if s in ("filings", "risks"):
            return [e for e in c.evidence.values() if e.provider in ("sec-edgar-fts", "sec-submissions")]
        if s in ("market", "valuation"):
            return [e for e in c.evidence.values() if e.provider in ("robinhood-mcp", "valuation-engine")]
        return []

    # financials
    def fin(self, metric: str) -> float | None:
        self._need("financials")
        f = self._ctx.fundamentals
        return f.metrics.get(metric) if f else None

    def fin_ev(self, metric: str) -> str | None:
        self._need("financials")
        f = self._ctx.fundamentals
        e = f.evidence.get(metric) if f else None
        return self._ctx.add(e).id if e else None

    def revenue_quarters(self):
        self._need("financials")
        f = self._ctx.fundamentals
        return list(f.revenue_q) if f else []

    # market / valuation
    def mkt(self) -> MarketData | None:
        self._need("market")
        return self._ctx.market

    def mkt_ev(self) -> str | None:
        self._need("market")
        return self._ctx.evidence.get(f"mkt:{self.ticker}") and f"mkt:{self.ticker}"

    def val(self) -> ValuationResult | None:
        self._need("valuation")
        return self._ctx.valuation

    def val_ev(self) -> str | None:
        self._need("valuation")
        return f"val:{self.ticker}" if f"val:{self.ticker}" in self._ctx.evidence else None

    # findings
    def findings(self, dimensions: set[str] | None = None, topics: set[str] | None = None,
                 keywords: tuple[str, ...] = (), max_age_days: int | None = None) -> list[tuple[Evidence, dict]]:
        self._need("findings")
        out = []
        for ev, raw in self._ctx.finding_ev:
            if dimensions and raw.get("dimension") not in dimensions:
                continue
            if topics and raw.get("topic") not in topics:
                continue
            if keywords and not any(k.lower() in raw.get("claim", "").lower() for k in keywords):
                continue
            if max_age_days is not None:
                pd = ev.published_date
                if pd is None or (self.as_of.date() - pd).days > max_age_days:
                    continue
            out.append((ev, raw))
        return out

    def raw_findings(self) -> AgentFindings | None:
        self._need("findings")
        return self._ctx.findings

    # policy
    def chains(self) -> list[PolicyChain]:
        self._need("policy")
        return list(self._ctx.policy_chains)

    def policy_events(self) -> list[PolicyEvent]:
        self._need("policy")
        return list(self._ctx.policy_events)

    def industries(self) -> set[str]:
        self._need("policy")
        return set(self._ctx.industries)

    # contracts
    def contracts(self) -> list[dict]:
        self._need("contracts")
        return list(self._ctx.contracts)

    # filings / risks
    def filings(self) -> list[dict]:
        self._need("filings")
        return list(self._ctx.filings)

    def filing_search(self, key: str) -> dict | None:
        if "filings" not in self._inputs and "risks" not in self._inputs:
            raise SliceAccessError("filings/risks slice not declared")
        return self._ctx.filing_searches.get(key)

    def agent_risks(self):
        self._need("risks")
        f = self._ctx.findings
        return list(f.key_risks) if f else []

    def dilution_events(self):
        self._need("risks")
        f = self._ctx.findings
        return list(f.dilution_events_last_12m) if f else []

    def going_concern_flag(self) -> bool | None:
        self._need("risks")
        f = self._ctx.findings
        return f.going_concern_warning if f else None

    def catalysts(self):
        self._need("catalysts")
        f = self._ctx.findings
        return list(f.upcoming_catalysts) if f else []

    def evidence(self, eid: str) -> Evidence | None:
        return self._ctx.evidence.get(eid)

    def register(self, ev: Evidence) -> str:
        return self._ctx.add(ev).id


def finding_to_evidence(ticker: str, raw: dict, provider: str) -> Evidence:
    return Evidence(
        ticker=ticker, claim=raw["claim"], source_url=raw["source_url"], source_title=raw.get("source_title", ""),
        published_date=raw.get("published_date"), evidence_type=EvidenceType(raw["evidence_type"]),
        provider=provider, sentiment=Sentiment(raw["sentiment"]), dimension=raw.get("dimension"),
        topic=raw.get("topic"),
    )


def domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def within(d: date | None, as_of: date, days: int) -> bool:
    return d is not None and timedelta(0) <= as_of - d <= timedelta(days=days)
