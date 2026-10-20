"""TikTok seller OSINT using public pages and indexed media."""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now

SEARCH_TERMS = [
    "Royale Diamonds TikTok",
    "RoyaleDiamonds lab grown",
    "Royale Diamonds auction",
    "Royale Diamonds scam",
    "Royale Diamonds review",
    "Royale Diamonds refund",
    "Royale Diamonds IGI",
    "Royale Diamonds shipping",
    "Royale Diamonds complaints",
    "Royale Diamonds Telegram",
]


def extract_profile_signals(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text("\n", strip=True)
    signals = {"page_title": title}
    # follower patterns from public web view
    m = re.search(
        r"(?P<name>RoyaleDiamonds)\s+(?P<user>royalediamondslive)\s+(?P<following>[\d.KMB]+)\s+Following\s+(?P<followers>[\d.KMB]+)\s+Followers\s+(?P<likes>[\d.KMB]+)\s+Likes",
        text,
        re.I,
    )
    if m:
        signals.update(m.groupdict())
    for pat, key in [
        (r"IGI certified[^\n]*", "bio_igi"),
        (r"CVD growth", "bio_cvd"),
        (r"Wholesale pricing[^\n]*", "bio_wholesale"),
        (r"IG\s*-\s*@[\w.]+", "bio_instagram"),
        (r"LIVE Event[^\n]*", "live_event"),
    ]:
        mm = re.search(pat, text, re.I)
        if mm:
            signals[key] = mm.group(0)
    return signals


def research_seller(
    name: str = "Royale Diamonds",
    username_hint: str | None = "royalediamondslive",
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "research" / "tiktok"
    out_dir.mkdir(parents=True, exist_ok=True)

    findings = {
        "seller_name_query": name,
        "confirmed_username": None,
        "confidence": "UNKNOWN",
        "profile": {},
        "media_corroboration": [],
        "search_terms": SEARCH_TERMS,
        "blocked": [],
        "name_collisions": [],
        "collected_at_utc": utc_now().isoformat(),
    }

    # Mashable is a primary public media source already observed to name the account.
    mashable = "https://mashable.com/life/tiktok-shop-lab-grown-diamond-live-auctions"
    mmeta = collector.get(mashable, cache_key="mashable_royale")
    if mmeta.get("content"):
        path, sha = collector.preserve("mashable_tiktok_auctions_pipeline.html", mmeta["content"])
        html = mmeta["content"].decode("utf-8", errors="ignore")
        users = sorted(set(re.findall(r"tiktok\.com/@([\w.]+)", html, flags=re.I)))
        if "royalediamondslive" in users or "@royalediamondslive" in html.lower():
            findings["confirmed_username"] = "royalediamondslive"
            findings["confidence"] = "HIGH"
            findings["media_corroboration"].append(
                {
                    "source": mashable,
                    "claim": "Mashable links Royale Diamonds livestreams to @royalediamondslive",
                    "status": "CORROBORATED",
                }
            )
        ledger.append(
            EvidenceRecord(
                evidence_id="media_mashable_royale",
                source_url=mashable,
                source_title="Mashable TikTok lab-grown diamond auctions",
                local_path=str(path),
                sha256=sha,
                source_category="media",
                reliability=Reliability.B,
                evidence_tier=EvidenceTier.SECONDARY,
                status=ClaimStatus.CORROBORATED,
                extracted_facts={"tiktok_usernames_linked": users},
                independently_corroborates=["tiktok_profile_royalediamondslive"],
            )
        )

    username = findings["confirmed_username"] or username_hint
    if username:
        profile_url = f"https://www.tiktok.com/@{username}"
        pmeta = collector.get(profile_url, cache_key=f"tiktok_{username}")
        if pmeta.get("http_status") == 200 and pmeta.get("content"):
            path, sha = collector.preserve(f"tiktok_{username}_pipeline.html", pmeta["content"])
            signals = extract_profile_signals(pmeta["content"].decode("utf-8", errors="ignore"))
            findings["profile"] = {"url": profile_url, **signals}
            findings["confirmed_username"] = username
            if findings["confidence"] == "UNKNOWN":
                findings["confidence"] = "MEDIUM"
            ledger.append(
                EvidenceRecord(
                    evidence_id=f"tiktok_profile_{username}",
                    source_url=profile_url,
                    source_title=signals.get("page_title", username),
                    local_path=str(path),
                    sha256=sha,
                    source_category="tiktok",
                    reliability=Reliability.B,
                    evidence_tier=EvidenceTier.PRIMARY,
                    status=ClaimStatus.CONFIRMED,
                    extracted_facts=signals,
                    notes="Public web profile only; video grid may fail without login.",
                )
            )
        else:
            findings["blocked"].append(
                {
                    "url": profile_url,
                    "reason": pmeta.get("error") or pmeta.get("status") or "http_error",
                }
            )

    # Document name collisions explicitly
    findings["name_collisions"] = [
        {
            "entity": "Royale Diamonds (Pune, India jewelry store)",
            "domain": "royalediamonds.com",
            "relation": "UNVERIFIED name collision — do not attribute to TikTok seller without proof",
            "status": "UNVERIFIED",
        },
        {
            "entity": "Royal Diamond USA LLC (Bellaire, TX consumer products)",
            "domain": "royaldiamondusa.com",
            "relation": "Different branding/products; not treated as same entity",
            "status": "IRRELEVANT_NAME_COLLISION",
        },
    ]

    out = out_dir / "seller_research.json"
    out.write_text(json.dumps(findings, indent=2))
    if owns:
        collector.close()
    return findings