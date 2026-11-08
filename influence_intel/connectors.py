"""Public-record connectors. All are keyless except FEC, which falls back to the rate-limited public DEMO_KEY."""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from silent_stocks.http import HOST_MIN_INTERVAL, CachedHttp, HttpError

from .models import ResearchDoc

HOST_MIN_INTERVAL.update({"lda.senate.gov": 0.5, "lda.gov": 0.5, "api.open.fec.gov": 0.5,
                          "projects.propublica.org": 0.5, "api.gdeltproject.org": 6.0})

LDA_FILINGS = "https://lda.senate.gov/api/v1/filings/"
PROPUBLICA_ORG = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
PROPUBLICA_SEARCH = "https://projects.propublica.org/nonprofits/api/v2/search.json"
FEC_BASE = "https://api.open.fec.gov/v1"
USASPENDING = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"

_PERIOD_Q = {"first_quarter": 1, "second_quarter": 2, "third_quarter": 3, "fourth_quarter": 4,
             "mid_year": 2, "year_end": 4}
BILL_RE = re.compile(r"(?<![\w.])(H\.\s?R\.|S\.|H\.\s?Res\.|S\.\s?Res\.|H\.\s?J\.\s?Res\.|S\.\s?J\.\s?Res\.)\s?(\d{1,5})\b")
# FEC entity types for organizations/committees. Individuals ("IND") are dropped at ingestion.
FEC_ORG_ENTITY_TYPES = {"CAN", "CCM", "COM", "ORG", "PAC", "PTY"}


BILL_TYPES = {"H.R.": "hr", "S.": "s", "H.Res.": "hres", "S.Res.": "sres", "H.J.Res.": "hjres", "S.J.Res.": "sjres"}
_CG_PATH = {"hr": "house-bill", "s": "senate-bill", "hres": "house-resolution", "sres": "senate-resolution",
            "hjres": "house-joint-resolution", "sjres": "senate-joint-resolution"}


def congress_for(year: int) -> int:
    return (year - 1789) // 2 + 1


def _bills(text: str, year: int) -> list[str]:
    """Bill numbers restart every Congress, so keys carry the Congress implied by the filing year."""
    c = congress_for(year)
    return sorted({f"{m.group(1).replace(' ', '')} {m.group(2)} ({c}th)" for m in BILL_RE.finditer(text or "")})


def parse_bill_key(key: str) -> tuple[int, str, int] | None:
    m = re.match(r"^(\S+) (\d+) \((\d+)th\)$", key)
    if not m or m.group(1) not in BILL_TYPES:
        return None
    return int(m.group(3)), BILL_TYPES[m.group(1)], int(m.group(2))


def bill_url(key: str) -> str | None:
    p = parse_bill_key(key)
    return f"https://www.congress.gov/bill/{p[0]}th-congress/{_CG_PATH[p[1]]}/{p[2]}" if p else None


class Congress:
    """congress.gov API (api.data.gov key; the public DEMO_KEY works at low volume)."""

    def __init__(self, http: CachedHttp, api_key: str | None = None):
        self.http = http
        self.api_key = api_key or os.environ.get("CONGRESS_API_KEY") or "DEMO_KEY"

    def status(self, key: str, as_of: date) -> dict | None:
        p = parse_bill_key(key)
        if not p:
            return None
        try:
            data, _ = self.http.get_json(f"https://api.congress.gov/v3/bill/{p[0]}/{p[1]}/{p[2]}", ttl_hours=24,
                                         params={"api_key": self.api_key, "format": "json"})
        except FileNotFoundError:
            return None
        b = data.get("bill") or {}
        la = b.get("latestAction") or {}
        la_date = date.fromisoformat(la["actionDate"]) if la.get("actionDate") else None
        # Only the latest action is fetched; if it postdates as_of the status at as_of is unknown.
        known = la_date is not None and la_date <= as_of
        laws = [x.get("number") for x in b.get("laws") or []]
        return {"key": key, "title": b.get("title"), "latest_action": la.get("text") if known else None,
                "latest_action_date": la_date if known else None, "enacted": bool(laws) if known else None,
                "public_law": laws[0] if laws and known else None, "url": bill_url(key)}


class Lda:
    def __init__(self, http: CachedHttp):
        self.http = http

    def filings(self, as_of: date, years: int = 3, client_names: list[str] = (), registrant_names: list[str] = ()) -> list[dict]:
        out: dict[str, dict] = {}
        queries = [("client_name", n) for n in client_names] + [("registrant_name", n) for n in registrant_names]
        for field, name in queries:
            for year in range(as_of.year - years + 1, as_of.year + 1):
                url, params = LDA_FILINGS, {field: name, "filing_year": year, "page_size": 25}
                while url:
                    data, _ = self.http.get_json(url, ttl_hours=24, params=params)
                    for r in data.get("results", []):
                        rec = self._parse(r)
                        if rec and rec["posted"] <= as_of:
                            out[rec["uuid"]] = rec
                    url, params = data.get("next"), None
        return sorted(out.values(), key=lambda r: (r["qkey"], r["uuid"]))

    @staticmethod
    def _parse(r: dict) -> dict | None:
        q = _PERIOD_Q.get(r.get("filing_period") or "")
        if not q or not r.get("dt_posted"):
            return None
        amount = r.get("income") or r.get("expenses")
        acts = r.get("lobbying_activities") or []
        text = " ".join(a.get("description") or "" for a in acts)
        year = int(r["filing_year"])
        return {
            "uuid": r["filing_uuid"], "year": int(r["filing_year"]), "quarter": q, "qkey": int(r["filing_year"]) * 4 + q - 1,
            "filing_type": r.get("filing_type"), "amount": float(amount) if amount else None,
            "client": (r.get("client") or {}).get("name"), "registrant": (r.get("registrant") or {}).get("name"),
            "in_house": ((r.get("client") or {}).get("name") or "").lower() == ((r.get("registrant") or {}).get("name") or "").lower(),
            "issue_codes": sorted({a["general_issue_code"] for a in acts if a.get("general_issue_code")}),
            "activities": [{"code": a.get("general_issue_code"), "description": (a.get("description") or "")[:500],
                            "bills": _bills(a.get("description") or "", year),
                            "government_entities": sorted({g["name"] for g in a.get("government_entities") or [] if g.get("name")}),
                            "lobbyist_count": len(a.get("lobbyists") or [])} for a in acts],
            "bills": _bills(text, year),
            "affiliated_organizations": sorted({o.get("name") for o in r.get("affiliated_organizations") or [] if o.get("name")}),
            "foreign_entities": sorted({o.get("name") for o in r.get("foreign_entities") or [] if o.get("name")}),
            "url": r.get("filing_document_url") or r.get("url"),
            "posted": datetime.fromisoformat(r["dt_posted"]).date(),
        }


class ProPublica:
    def __init__(self, http: CachedHttp):
        self.http = http

    def search(self, query: str) -> list[dict]:
        data, _ = self.http.get_json(PROPUBLICA_SEARCH, ttl_hours=168, params={"q": query})
        return [{"ein": o.get("ein"), "name": o.get("name"), "state": o.get("state"), "ntee_code": o.get("ntee_code")}
                for o in data.get("organizations", [])]

    def filings(self, ein: int, as_of: date) -> list[dict]:
        try:
            data, _ = self.http.get_json(PROPUBLICA_ORG.format(ein=ein), ttl_hours=168)
        except FileNotFoundError:
            return []
        org = data.get("organization") or {}
        out = []
        for f in data.get("filings_with_data") or []:
            prd = str(f.get("tax_prd") or "")
            if len(prd) != 6:
                continue
            end = date(int(prd[:4]), int(prd[4:]), 28)
            # Form 990s are due ~4.5 months after period end (plus extensions); treat as public 10 months after.
            if end + timedelta(days=300) > as_of:
                continue
            out.append({"ein": ein, "name": org.get("name"), "period_end": end, "year": int(prd[:4]),
                        "revenue": f.get("totrevenue"), "expenses": f.get("totfuncexpns"), "assets": f.get("totassetsend"),
                        "contributions": f.get("totcntrbgfts"), "form": f.get("formtype"),
                        "url": f.get("pdf_url") or f"https://projects.propublica.org/nonprofits/organizations/{ein}"})
        return sorted(out, key=lambda r: r["period_end"])


class Fec:
    def __init__(self, http: CachedHttp, api_key: str | None = None):
        self.http = http
        self.api_key = api_key or os.environ.get("FEC_API_KEY") or "DEMO_KEY"

    def disbursements(self, committee_id: str, as_of: date, cycles: int = 2, max_pages: int = 5) -> list[dict]:
        out = []
        first = as_of.year + (as_of.year % 2)
        for cycle in range(first - 2 * (cycles - 1), first + 1, 2):
            params = {"committee_id": committee_id, "two_year_transaction_period": cycle, "per_page": 100,
                      "sort": "-disbursement_date", "api_key": self.api_key}
            for _ in range(max_pages):
                data, _ = self.http.get_json(f"{FEC_BASE}/schedules/schedule_b/", ttl_hours=24, params=params)
                for r in data.get("results", []):
                    if (r.get("entity_type") or "").upper() not in FEC_ORG_ENTITY_TYPES:
                        continue
                    d = r.get("disbursement_date")
                    d = date.fromisoformat(d[:10]) if d else None
                    if d is None or d > as_of:
                        continue
                    out.append({"committee_id": committee_id, "recipient": r.get("recipient_name"),
                                "recipient_committee_id": r.get("recipient_committee_id"),
                                "entity_type": r.get("entity_type"), "amount": float(r.get("disbursement_amount") or 0),
                                "date": d, "purpose": r.get("disbursement_description"), "cycle": cycle,
                                "url": f"https://www.fec.gov/data/disbursements/?committee_id={committee_id}&two_year_transaction_period={cycle}"})
                last = (data.get("pagination") or {}).get("last_indexes")
                if not last or not data.get("results"):
                    break
                params = {**params, **last}
        return out


class Awards:
    GROUPS = {"grant": ["02", "03", "04", "05"], "contract": ["A", "B", "C", "D"]}

    def __init__(self, http: CachedHttp):
        self.http = http

    def search(self, name: str, as_of: date, lookback_days: int = 3 * 365, limit: int = 25) -> list[dict]:
        out = []
        for kind, codes in self.GROUPS.items():
            body = {"filters": {"recipient_search_text": [name], "award_type_codes": codes,
                                "time_period": [{"start_date": (as_of - timedelta(days=lookback_days)).isoformat(),
                                                 "end_date": as_of.isoformat()}]},
                    "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Start Date", "Description",
                               "generated_internal_id"],
                    "sort": "Award Amount", "order": "desc", "limit": limit, "page": 1}
            data, _ = self.http.post_json(USASPENDING, body, ttl_hours=24)
            token = name.split()[0].lower()
            for r in data.get("results", []):
                if token not in (r.get("Recipient Name") or "").lower():
                    continue
                sd = r.get("Start Date")
                gid = r.get("generated_internal_id")
                out.append({"kind": kind, "award_id": r.get("Award ID"), "recipient": r.get("Recipient Name"),
                            "amount": float(r.get("Award Amount") or 0), "agency": r.get("Awarding Agency"),
                            "start_date": date.fromisoformat(sd) if sd else None, "description": r.get("Description"),
                            "url": f"https://www.usaspending.gov/award/{gid}" if gid else "https://www.usaspending.gov/search"})
        return out


class News:
    """GDELT 2.0 DOC API: coverage volume (share of monitored articles) and average tone, last 12 months."""

    def __init__(self, http: CachedHttp):
        self.http = http

    def timeline(self, query: str, mode: str) -> list[tuple[date, float]]:
        data, _ = self.http.get_json(GDELT, ttl_hours=24, params={"query": query, "mode": mode, "timespan": "12m", "format": "json"})
        series = (data.get("timeline") or [{}])[0].get("data") or []
        return [(datetime.strptime(p["date"][:8], "%Y%m%d").date(), float(p["value"])) for p in series]

    def summary(self, query: str, as_of: date) -> dict | None:
        try:
            vol = [p for p in self.timeline(query, "timelinevol") if p[0] <= as_of]
            tone = [p for p in self.timeline(query, "timelinetone") if p[0] <= as_of]
        except HttpError:
            return None
        if not vol:
            return None

        def avg(pts, lo, hi):
            v = [x for d, x in pts if lo < (as_of - d).days <= hi]
            return sum(v) / len(v) if v else None

        return {"query": query, "volume_recent_90d": avg(vol, -1, 90), "volume_prior_90d": avg(vol, 90, 180),
                "tone_recent_90d": avg(tone, -1, 90), "tone_prior_90d": avg(tone, 90, 180),
                "url": f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=timelinevol&timespan=12m"}


def load_research(path: Path, as_of: date) -> ResearchDoc | None:
    """Point-in-time: a research file researched after as_of is ignored, and so is any item published after as_of."""
    if not path.exists():
        return None
    doc = ResearchDoc.model_validate(json.loads(path.read_text()))
    if doc.researched_at.date() > as_of:
        return None
    keep = lambda d: d is None or d <= as_of  # noqa: E731
    doc.findings = [f for f in doc.findings if keep(f.published_date)]
    doc.initiatives = [i for i in doc.initiatives if keep(i.published_date)]
    doc.alliances = [a for a in doc.alliances if keep(a.since)]
    return doc
