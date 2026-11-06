"""Market data connectors.

The Robinhood MCP is reachable only from an MCP-capable agent session, not from this Python process. The agent
captures MCP responses into dated JSON snapshots under data/snapshots/robinhood/<date>/; this connector reads them
with full provenance and the original quote timestamps, so stale prices are detectable.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import log, sqrt
from pathlib import Path
from typing import Protocol

from ..http import CachedHttp


@dataclass
class MarketData:
    ticker: str
    company: str | None
    price: float | None
    price_time: datetime | None
    source: str
    market_cap: float | None = None
    shares_outstanding: float | None = None
    float_shares: float | None = None
    avg_volume_30d: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    sector: str | None = None
    industry: str | None = None
    hq: str | None = None
    employees: int | None = None
    price_12m_ago: float | None = None
    monthly_closes: list[float] = field(default_factory=list)
    snapshot_file: str | None = None
    is_demo: bool = False
    listing_status: str | None = None

    @property
    def return_12m(self) -> float | None:
        if self.price and self.price_12m_ago:
            return self.price / self.price_12m_ago - 1
        return None

    @property
    def annual_volatility(self) -> float | None:
        closes = [c for c in self.monthly_closes if c and c > 0]
        if self.price:
            closes = closes + [self.price]
        if len(closes) < 6:
            return None
        rets = [log(b / a) for a, b in zip(closes, closes[1:])]
        return statistics.stdev(rets) * sqrt(12)

    @property
    def turnover_daily(self) -> float | None:
        if self.avg_volume_30d and self.float_shares:
            return self.avg_volume_30d / self.float_shares
        return None

    def age_hours(self, now: datetime) -> float | None:
        if not self.price_time:
            return None
        return (now - self.price_time).total_seconds() / 3600


class MarketDataConnector(Protocol):
    name: str

    def get(self, ticker: str) -> MarketData | None: ...

    def tickers(self) -> list[str]: ...


def _parse_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _record_to_market(ticker: str, rec: dict, source: str, path: Path, is_demo: bool) -> MarketData:
    return MarketData(
        ticker=ticker,
        company=rec.get("company"),
        price=rec.get("price"),
        price_time=_parse_time(rec.get("price_time")),
        source=source,
        market_cap=rec.get("market_cap"),
        shares_outstanding=rec.get("shares_outstanding"),
        float_shares=rec.get("float"),
        avg_volume_30d=rec.get("avg_volume_30d"),
        high_52w=rec.get("high_52w"),
        low_52w=rec.get("low_52w"),
        pe_ratio=rec.get("pe_ratio"),
        pb_ratio=rec.get("pb_ratio"),
        sector=rec.get("sector"),
        industry=rec.get("industry"),
        hq=rec.get("hq"),
        employees=rec.get("employees"),
        price_12m_ago=rec.get("price_12m_ago"),
        monthly_closes=list(rec.get("monthly_closes") or []),
        snapshot_file=str(path),
        is_demo=is_demo,
        listing_status=rec.get("listing_status"),
    )


class SnapshotMarketConnector:
    """Reads every snapshot file; for each ticker the record with the newest price_time wins."""

    def __init__(self, snapshot_dir: Path, name: str = "robinhood-mcp-snapshot", is_demo: bool = False):
        self.name = name
        self.snapshot_dir = snapshot_dir
        self.is_demo = is_demo
        self._data: dict[str, MarketData] = {}
        self.benchmarks: dict[str, dict] = {}
        self.positions: dict | None = None
        self._load()

    def _load(self) -> None:
        if not self.snapshot_dir.exists():
            return
        for path in sorted(self.snapshot_dir.rglob("*.json")):
            doc = json.loads(path.read_text())
            source = f"{doc.get('source', self.name)}@{doc.get('captured_at', '?')}"
            if "positions" in doc:
                if self.positions is None or doc.get("captured_at", "") >= self.positions.get("captured_at", ""):
                    self.positions = doc
            for ticker, rec in (doc.get("securities") or {}).items():
                md = _record_to_market(ticker.upper(), rec, source, path, self.is_demo or doc.get("demo", False))
                cur = self._data.get(md.ticker)
                if cur is None or (md.price_time and cur.price_time and md.price_time > cur.price_time) or cur.price_time is None:
                    self._data[md.ticker] = md
            self.benchmarks.update(doc.get("benchmarks") or {})
        if self.positions:
            when = _parse_time(self.positions.get("captured_at"))
            src = f"{self.positions.get('source', self.name)}:positions@{self.positions.get('captured_at', '?')}"
            for h in self.positions["positions"].get("holdings", []):
                t = h["symbol"].upper()
                if t not in self._data and h.get("price"):
                    self._data[t] = MarketData(ticker=t, company=None, price=float(h["price"]), price_time=when,
                                               source=src, monthly_closes=list(h.get("monthly_closes") or []),
                                               snapshot_file=None, is_demo=self.is_demo or self.positions.get("demo", False))

    def get(self, ticker: str) -> MarketData | None:
        return self._data.get(ticker.upper())

    def tickers(self) -> list[str]:
        return sorted(self._data)


class PolygonConnector:
    """Production connector for Polygon.io (requires POLYGON_API_KEY). Provides price, market cap and shares."""

    name = "polygon"

    def __init__(self, http: CachedHttp, api_key: str):
        self.http = http
        self.api_key = api_key

    def get(self, ticker: str) -> MarketData | None:
        prev, _ = self.http.get_json(
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev", ttl_hours=1, params={"apiKey": self.api_key}
        )
        results = prev.get("results") or []
        if not results:
            return None
        bar = results[0]
        ref, _ = self.http.get_json(
            f"https://api.polygon.io/v3/reference/tickers/{ticker}", ttl_hours=24, params={"apiKey": self.api_key}
        )
        info = ref.get("results") or {}
        return MarketData(
            ticker=ticker,
            company=info.get("name"),
            price=bar.get("c"),
            price_time=datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc),
            source="polygon",
            market_cap=info.get("market_cap"),
            shares_outstanding=info.get("weighted_shares_outstanding"),
            avg_volume_30d=bar.get("v"),
        )

    def tickers(self) -> list[str]:
        return []


class ChainedMarketConnector:
    def __init__(self, connectors: list):
        self.connectors = connectors
        self.name = "+".join(c.name for c in connectors)

    def get(self, ticker: str) -> MarketData | None:
        for c in self.connectors:
            try:
                md = c.get(ticker)
            except Exception:  # noqa: BLE001 - a failing provider falls through to the next one
                md = None
            if md and md.price is not None:
                return md
        return None

    def tickers(self) -> list[str]:
        out: set[str] = set()
        for c in self.connectors:
            out.update(c.tickers())
        return sorted(out)
