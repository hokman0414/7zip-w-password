"""SEC EDGAR connector: ticker map, XBRL company facts, frames (cross-sectional), submissions, full-text search."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from ..http import CachedHttp

TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/{taxonomy}/{concept}/{unit}/{period}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FTS_URL = "https://efts.sec.gov/LATEST/search-index"
LISTED_EXCHANGES = {"Nasdaq", "NYSE", "NYSE American", "NYSE Arca", "Cboe BZX"}


def filing_index_url(cik: int, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"


@dataclass
class Listing:
    cik: int
    name: str
    ticker: str
    exchange: str | None


class SecEdgar:
    def __init__(self, http: CachedHttp):
        self.http = http
        self._listings: dict[str, Listing] | None = None

    def listings(self) -> dict[str, Listing]:
        if self._listings is None:
            data, _ = self.http.get_json(TICKERS_URL, ttl_hours=24 * 7)
            fields = data["fields"]
            out: dict[str, Listing] = {}
            for row in data["data"]:
                rec = dict(zip(fields, row))
                ticker = str(rec["ticker"]).upper()
                out.setdefault(ticker, Listing(int(rec["cik"]), rec["name"], ticker, rec.get("exchange")))
            self._listings = out
        return self._listings

    def cik_for(self, ticker: str) -> int | None:
        listing = self.listings().get(ticker.upper())
        return listing.cik if listing else None

    def company_facts(self, cik: int) -> tuple[dict, dict]:
        return self.http.get_json(FACTS_URL.format(cik=cik), ttl_hours=24)

    def submissions(self, cik: int) -> tuple[dict, dict]:
        return self.http.get_json(SUBMISSIONS_URL.format(cik=cik), ttl_hours=24)

    def frame(self, concept: str, period: str, unit: str = "USD", taxonomy: str = "us-gaap") -> tuple[list[dict], dict]:
        try:
            data, prov = self.http.get_json(
                FRAMES_URL.format(taxonomy=taxonomy, concept=concept, unit=unit, period=period), ttl_hours=24 * 3
            )
        except FileNotFoundError:
            return [], {"url": FRAMES_URL.format(taxonomy=taxonomy, concept=concept, unit=unit, period=period)}
        return data.get("data", []), prov

    def recent_filings(self, cik: int, as_of: date, forms: set[str] | None = None, limit: int = 40) -> list[dict]:
        data, _ = self.submissions(cik)
        recent = data.get("filings", {}).get("recent", {})
        rows = []
        for i, form in enumerate(recent.get("form", [])):
            filed = date.fromisoformat(recent["filingDate"][i])
            if filed > as_of or (forms and form not in forms):
                continue
            accn = recent["accessionNumber"][i]
            rows.append(
                {
                    "form": form,
                    "filed": filed,
                    "accession": accn,
                    "primary_document": recent["primaryDocument"][i],
                    "description": recent.get("primaryDocDescription", [""] * (i + 1))[i],
                    "items": recent.get("items", [""] * (i + 1))[i],
                    "url": filing_index_url(cik, accn) + recent["primaryDocument"][i],
                }
            )
            if len(rows) >= limit:
                break
        return rows

    def full_text_search(self, phrase: str, cik: int, start: date, end: date, forms: str = "10-K,10-Q,8-K") -> list[dict]:
        params = {
            "q": f'"{phrase}"',
            "ciks": f"{cik:010d}",
            "forms": forms,
            "dateRange": "custom",
            "startdt": start.isoformat(),
            "enddt": end.isoformat(),
        }
        data, _ = self.http.get_json(FTS_URL, ttl_hours=24, params=params)
        hits = []
        for hit in data.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            accn, _, fname = hit.get("_id", "").partition(":")
            hits.append(
                {
                    "form": src.get("form") or (src.get("root_forms") or [""])[0],
                    "filed": src.get("file_date"),
                    "accession": accn,
                    "url": filing_index_url(cik, accn) + fname if accn else "",
                }
            )
        return hits


def facts_for(facts: dict, concept: str, taxonomy: str = "us-gaap", unit: str | None = None) -> list[dict[str, Any]]:
    node = facts.get("facts", {}).get(taxonomy, {}).get(concept)
    if not node:
        return []
    units = node.get("units", {})
    if unit:
        return list(units.get(unit, []))
    for preferred in ("USD", "shares", "pure"):
        if preferred in units:
            return list(units[preferred])
    return list(next(iter(units.values()), []))
