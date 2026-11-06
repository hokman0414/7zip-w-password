"""HTTP client with file cache, retries, per-host rate limits and provenance logging."""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

# SEC fair-access policy is 10 requests/second; stay well under it.
HOST_MIN_INTERVAL = {"data.sec.gov": 0.15, "www.sec.gov": 0.15, "efts.sec.gov": 0.2, "api.usaspending.gov": 0.3}


class HttpError(RuntimeError):
    pass


class CachedHttp:
    def __init__(self, cache_dir: Path, user_agent: str, timeout: float = 30.0, offline: bool = False):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline = offline
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
            follow_redirects=True,
        )
        self._last_call: dict[str, float] = {}
        self._lock = threading.Lock()

    def _cache_path(self, method: str, url: str, body: Any) -> Path:
        key = hashlib.sha256(f"{method}|{url}|{json.dumps(body, sort_keys=True)}".encode()).hexdigest()
        return self.cache_dir / key[:2] / f"{key}.json"

    def _throttle(self, url: str) -> None:
        host = urlparse(url).netloc
        interval = HOST_MIN_INTERVAL.get(host, 0.1)
        with self._lock:
            wait = self._last_call.get(host, 0.0) + interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_call[host] = time.monotonic()

    def get_json(self, url: str, ttl_hours: float = 24.0, params: dict | None = None) -> tuple[Any, dict]:
        return self._request("GET", url, ttl_hours, params=params)

    def post_json(self, url: str, body: dict, ttl_hours: float = 24.0) -> tuple[Any, dict]:
        return self._request("POST", url, ttl_hours, body=body)

    def _request(self, method: str, url: str, ttl_hours: float, params: dict | None = None, body: Any = None):
        full_key = url + ("?" + json.dumps(params, sort_keys=True) if params else "")
        path = self._cache_path(method, full_key, body)
        if path.exists():
            cached = json.loads(path.read_text())
            age_h = (time.time() - cached["provenance"]["retrieved_epoch"]) / 3600
            if age_h <= ttl_hours or self.offline:
                cached["provenance"]["from_cache"] = True
                return cached["data"], cached["provenance"]
        if self.offline:
            raise HttpError(f"offline and no cache for {url}")
        last_exc: Exception | None = None
        for attempt in range(4):
            self._throttle(url)
            try:
                resp = self._client.request(method, url, params=params, json=body)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise HttpError(f"{resp.status_code} from {url}")
                if resp.status_code == 404:
                    raise FileNotFoundError(url)
                resp.raise_for_status()
                data = resp.json()
                provenance = {
                    "url": str(resp.url),
                    "method": method,
                    "status": resp.status_code,
                    "retrieved_epoch": time.time(),
                    "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "from_cache": False,
                }
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"provenance": provenance, "data": data}))
                return data, provenance
            except FileNotFoundError:
                raise
            except (httpx.HTTPError, HttpError, json.JSONDecodeError) as exc:
                last_exc = exc
                backoff = 2**attempt
                log.warning("request failed (%s), retry in %ss: %s", exc, backoff, url)
                time.sleep(backoff)
        raise HttpError(f"giving up on {url}: {last_exc}")
