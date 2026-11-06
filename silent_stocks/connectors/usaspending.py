"""USAspending.gov connector: federal contract awards by recipient name (no API key required)."""
from __future__ import annotations

import re
from datetime import date, timedelta

from ..http import CachedHttp

AWARDS_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
CONTRACT_CODES = ["A", "B", "C", "D"]
_SUFFIXES = re.compile(r"\b(inc|incorporated|corp|corporation|co|company|holdings|group|ltd|llc|plc|the)\b\.?", re.I)


def recipient_search_name(company_name: str) -> str:
    cleaned = _SUFFIXES.sub(" ", company_name.replace(",", " ").replace("&", " "))
    return " ".join(cleaned.split())


class UsaSpending:
    def __init__(self, http: CachedHttp):
        self.http = http

    def contract_awards(self, company_name: str, as_of: date, lookback_days: int = 365, limit: int = 25) -> list[dict]:
        """Name-matched awards. Recipient matching is textual, so results are labeled as requiring verification."""
        name = recipient_search_name(company_name)
        if len(name) < 3:
            return []
        body = {
            "filters": {
                "recipient_search_text": [name],
                "award_type_codes": CONTRACT_CODES,
                "time_period": [{"start_date": (as_of - timedelta(days=lookback_days)).isoformat(), "end_date": as_of.isoformat()}],
            },
            "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Start Date", "Description", "generated_internal_id"],
            "sort": "Award Amount",
            "order": "desc",
            "limit": limit,
            "page": 1,
        }
        data, _ = self.http.post_json(AWARDS_URL, body, ttl_hours=24)
        first_token = name.split()[0].lower()
        awards = []
        for row in data.get("results", []):
            recipient = (row.get("Recipient Name") or "").lower()
            if first_token not in recipient:
                continue
            internal = row.get("generated_internal_id")
            awards.append(
                {
                    "award_id": row.get("Award ID"),
                    "recipient": row.get("Recipient Name"),
                    "amount": float(row.get("Award Amount") or 0.0),
                    "agency": row.get("Awarding Agency"),
                    "start_date": row.get("Start Date"),
                    "description": row.get("Description"),
                    "url": f"https://www.usaspending.gov/award/{internal}" if internal else "https://www.usaspending.gov/search",
                }
            )
        return awards
