from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup

from cyber_talks.models import TalkCandidate

log = logging.getLogger(__name__)

BASE = "https://allbsides.com"
UA = {"User-Agent": "cyber-talks-pipeline/0.1 (research; +local)"}


def _client() -> httpx.Client:
    return httpx.Client(timeout=45.0, headers=UA, follow_redirects=True)


def _extract_youtube_id(href: str | None) -> str | None:
    if not href:
        return None
    m = re.search(r"(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})", href)
    if m:
        return m.group(1)
    m2 = re.search(r"/talk/([A-Za-z0-9_-]{11})\.html", href)
    return m2.group(1) if m2 else None


def list_talk_urls_from_sitemap(client: httpx.Client | None = None, limit: int | None = None) -> list[str]:
    owns = client is None
    client = client or _client()
    urls: list[str] = []
    try:
        r = client.get(f"{BASE}/sitemap.xml")
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in root.findall(".//sm:url/sm:loc", ns):
            if loc.text and "/talk/" in loc.text:
                urls.append(loc.text.strip())
                if limit and len(urls) >= limit:
                    break
        if not urls:
            # fallback without namespace
            for loc in root.iter():
                if loc.tag.endswith("loc") and loc.text and "/talk/" in loc.text:
                    urls.append(loc.text.strip())
                    if limit and len(urls) >= limit:
                        break
    finally:
        if owns:
            client.close()
    return urls


def search_allbsides(
    query: str,
    *,
    client: httpx.Client | None = None,
    limit: int = 40,
) -> list[TalkCandidate]:
    """Best-effort scrape of allbsides.com search/listing for BSides talks."""
    owns = client is None
    client = client or _client()
    candidates: list[TalkCandidate] = []
    try:
        q = quote_plus(query)
        urls = [f"{BASE}/?q={q}", f"{BASE}/search?q={q}", BASE]
        html = ""
        for url in urls:
            try:
                r = client.get(url)
                if r.status_code == 200 and len(r.text) > 500:
                    html = r.text
                    break
            except httpx.HTTPError as exc:
                log.debug("allbsides fetch %s: %s", url, exc)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/talk/" not in href:
                continue
            vid = _extract_youtube_id(href)
            if not vid:
                continue
            title = a.get_text(" ", strip=True)
            if not title or len(title) < 8:
                continue
            full = urljoin(BASE, href)
            candidates.append(
                TalkCandidate(
                    video_id=vid,
                    title=title,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    description=f"Listed on AllBSides: {full}",
                    channel="AllBSides",
                    conference_id="media-allbsides",
                    conference_name="AllBSides aggregator",
                    discovery_method="allbsides",
                    raw={"allbsides_url": full},
                )
            )
            if len(candidates) >= limit:
                break
        time.sleep(0.3)
    finally:
        if owns:
            client.close()

    dedup: dict[str, TalkCandidate] = {}
    for c in candidates:
        dedup.setdefault(c.video_id, c)
    return list(dedup.values())


def discover_allbsides_sitemap(
    *,
    limit: int | None = 500,
    topic_filter: str | None = None,
) -> list[TalkCandidate]:
    """Enumerate AllBSides talk URLs from sitemap (fast bulk discovery)."""
    client = _client()
    out: list[TalkCandidate] = []
    try:
        urls = list_talk_urls_from_sitemap(client, limit=limit)
        for u in urls:
            vid = _extract_youtube_id(u)
            if not vid:
                continue
            # Title unknown until page fetch; use video id placeholder filtered later via enrich
            title = f"AllBSides talk {vid}"
            if topic_filter and topic_filter.lower() not in u.lower():
                pass
            out.append(
                TalkCandidate(
                    video_id=vid,
                    title=title,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    description=f"Listed on AllBSides: {u}",
                    channel="AllBSides",
                    conference_id="media-allbsides",
                    conference_name="AllBSides aggregator",
                    discovery_method="allbsides_sitemap",
                    raw={"allbsides_url": u},
                )
            )
    finally:
        client.close()
    return out


def fetch_allbsides_talk(talk_url_or_id: str, client: httpx.Client | None = None) -> dict[str, Any]:
    """
    Fetch metadata + on-page transcript from an AllBSides talk page.
    talk_url_or_id: full URL or 11-char youtube id.
    """
    owns = client is None
    client = client or _client()
    if talk_url_or_id.startswith("http"):
        url = talk_url_or_id
        vid = _extract_youtube_id(url) or ""
    else:
        vid = talk_url_or_id
        url = f"{BASE}/talk/{vid}.html"
    try:
        r = client.get(url)
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "url": url}
        soup = BeautifulSoup(r.text, "lxml")
        h1 = soup.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else ""
        # Conference often near title
        conf = None
        for a in soup.find_all("a", href=True):
            t = a.get_text(" ", strip=True)
            if t.lower().startswith("bsides") or "BSides" in t:
                conf = t
                break
        body = soup.select_one(".transcript-body")
        transcript = body.get_text(" ", strip=True) if body else ""
        # About / description
        about = ""
        for label in soup.find_all(string=re.compile(r"About this talk", re.I)):
            parent = label.parent
            if parent and parent.find_next_sibling():
                about = parent.find_next_sibling().get_text(" ", strip=True)
                break
        if not about:
            # fallback: meta description
            md = soup.find("meta", attrs={"name": "description"})
            if md and md.get("content"):
                about = md["content"]

        people: list[str] = []
        text = soup.get_text("\n", strip=True)
        m = re.search(r"People\s*\n(.+?)(?:\nShow transcript|\nRelated|$)", text, re.S)
        if m:
            for piece in re.split(r"\s{2,}|\n", m.group(1)):
                piece = piece.strip()
                if 2 < len(piece) < 80 and not piece.startswith("About"):
                    people.append(piece)

        published = None
        pm = re.search(r"Published\s+(\d{4}-\d{2})", text)
        if pm:
            published = pm.group(1).replace("-", "") + "01"

        return {
            "ok": True,
            "url": url,
            "video_id": vid,
            "title": title,
            "conference": conf,
            "description": about,
            "speakers": people,
            "upload_date": published,
            "transcript": transcript,
            "transcript_source": "allbsides_page" if len(transcript) > 100 else "none",
        }
    except Exception as exc:  # noqa: BLE001
        log.info("allbsides talk fetch fail %s: %s", url, exc)
        return {"ok": False, "error": str(exc), "url": url}
    finally:
        if owns:
            client.close()


# Back-compat alias
def fetch_allbsides_transcript_page(talk_url: str, client: httpx.Client | None = None) -> dict[str, Any]:
    data = fetch_allbsides_talk(talk_url, client=client)
    return {
        "text": data.get("transcript") or "",
        "source": data.get("transcript_source") or "none",
        "error": data.get("error"),
        **data,
    }
