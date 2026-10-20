"""HTTP helpers with caching, backoff, and robots.txt awareness."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from src.evidence_ledger import RAW_DIR, sha256_bytes

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "http_cache"
UA = "RoyaleDiamondsOSINT/1.0 (+research; respectful; contact: local)"


class HttpCollector:
    def __init__(self, timeout: float = 30.0, min_delay: float = 0.8):
        self.timeout = timeout
        self.min_delay = min_delay
        self._last_host_ts: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"},
        )

    def close(self) -> None:
        self.client.close()

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots:
            rp = RobotFileParser()
            try:
                rp.set_url(f"{base}/robots.txt")
                rp.read()
            except Exception:
                # If robots cannot be fetched, proceed cautiously but allow public GETs.
                self._robots[base] = RobotFileParser()
                return True
            self._robots[base] = rp
        rp = self._robots[base]
        try:
            return rp.can_fetch(UA, url)
        except Exception:
            return True

    def _throttle(self, url: str) -> None:
        host = urlparse(url).netloc
        last = self._last_host_ts.get(host, 0.0)
        wait = self.min_delay - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        self._last_host_ts[host] = time.time()

    def get(
        self,
        url: str,
        *,
        cache_key: Optional[str] = None,
        retries: int = 3,
        respect_robots: bool = True,
    ) -> dict:
        if respect_robots and not self.allowed(url):
            return {
                "url": url,
                "status": "robots_disallowed",
                "http_status": None,
                "content": b"",
                "error": "robots.txt disallows this User-Agent path",
            }

        cache_path = CACHE_DIR / f"{cache_key or sha256_bytes(url.encode())[:16]}.meta.json"
        body_path = CACHE_DIR / f"{cache_key or sha256_bytes(url.encode())[:16]}.body"
        if cache_path.exists() and body_path.exists():
            meta = json.loads(cache_path.read_text())
            meta["content"] = body_path.read_bytes()
            meta["cached"] = True
            return meta

        last_error = None
        for attempt in range(retries):
            self._throttle(url)
            try:
                resp = self.client.get(url)
                meta = {
                    "url": url,
                    "final_url": str(resp.url),
                    "http_status": resp.status_code,
                    "content_type": resp.headers.get("content-type", ""),
                    "status": "ok" if resp.status_code < 400 else "http_error",
                    "content": resp.content,
                    "sha256": sha256_bytes(resp.content),
                    "cached": False,
                }
                body_path.write_bytes(resp.content)
                cache_path.write_text(
                    json.dumps({k: v for k, v in meta.items() if k != "content"}, indent=2)
                )
                return meta
            except Exception as e:
                last_error = repr(e)
                time.sleep(2**attempt)
        return {
            "url": url,
            "status": "error",
            "http_status": None,
            "content": b"",
            "error": last_error,
        }

    def preserve(self, filename: str, content: bytes) -> tuple[Path, str]:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        path = RAW_DIR / filename
        path.write_bytes(content)
        return path, sha256_bytes(content)