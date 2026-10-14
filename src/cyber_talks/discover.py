from __future__ import annotations

import json
import logging
import shlex
import subprocess
import time
from typing import Any, Iterable

from cyber_talks.models import Conference, TalkCandidate

log = logging.getLogger(__name__)


def _run_yt_dlp(args: list[str], timeout: int = 180) -> list[dict[str, Any]]:
    """Run yt-dlp -J / -j and return list of entry dicts."""
    cmd = ["yt-dlp", "--ignore-errors", "--no-warnings", *args]
    log.debug("yt-dlp: %s", " ".join(shlex.quote(a) for a in cmd))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError("yt-dlp is not installed or not on PATH") from e
    except subprocess.TimeoutExpired:
        log.warning("yt-dlp timed out: %s", cmd[-1] if cmd else "")
        return []

    if proc.returncode not in (0, 1):  # 1 often means partial success with --ignore-errors
        log.warning("yt-dlp rc=%s stderr=%s", proc.returncode, (proc.stderr or "")[:500])

    text = (proc.stdout or "").strip()
    if not text:
        return []

    # -J emits one JSON object; -j emits NDJSON
    if text.startswith("{"):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            # Might be concatenated objects; fall through to NDJSON parse
            obj = None
        if obj is not None:
            if "entries" in obj:
                return [e for e in (obj.get("entries") or []) if e]
            return [obj]

    entries: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _entry_to_candidate(
    entry: dict[str, Any],
    *,
    conference: Conference | None = None,
    discovery_method: str = "unknown",
) -> TalkCandidate | None:
    video_id = entry.get("id") or entry.get("url")
    if not video_id:
        return None
    # playlist entries sometimes nest
    if entry.get("_type") == "url" and not entry.get("title"):
        return None
    title = entry.get("title") or entry.get("fulltitle") or ""
    if not title:
        return None
    url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"
    if "youtube.com" not in url and "youtu.be" not in url:
        # Normalize pure IDs
        if len(str(video_id)) == 11:
            url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            return None
    # Extract 11-char id when possible
    vid = str(video_id)
    if "watch?v=" in url:
        vid = url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0]

    upload = entry.get("upload_date")
    if not upload and entry.get("release_timestamp"):
        try:
            from datetime import datetime, timezone

            upload = datetime.fromtimestamp(int(entry["release_timestamp"]), tz=timezone.utc).strftime(
                "%Y%m%d"
            )
        except (TypeError, ValueError, OSError):
            upload = None

    return TalkCandidate(
        video_id=vid,
        title=title,
        url=url if url.startswith("http") else f"https://www.youtube.com/watch?v={vid}",
        description=entry.get("description") or "",
        channel=entry.get("channel") or entry.get("uploader") or "",
        channel_id=entry.get("channel_id") or "",
        upload_date=upload,
        duration_seconds=entry.get("duration"),
        view_count=entry.get("view_count"),
        conference_id=conference.id if conference else None,
        conference_name=conference.name if conference else None,
        discovery_method=discovery_method,
        raw={"id": vid, "extractor": entry.get("extractor")},
    )


def discover_channel(
    handle_or_url: str,
    *,
    conference: Conference | None = None,
    playlist_end: int = 80,
    sleep_s: float = 0.5,
) -> list[TalkCandidate]:
    """List recent uploads from a YouTube channel handle (@name) or URL."""
    target = handle_or_url.strip()
    if target.startswith("@"):
        url = f"https://www.youtube.com/{target}/videos"
    elif target.startswith("http"):
        url = target
    else:
        url = f"https://www.youtube.com/@{target}/videos"

    entries = _run_yt_dlp(
        [
            "--flat-playlist",
            "--playlist-end",
            str(playlist_end),
            "-J",
            url,
        ],
        timeout=240,
    )
    time.sleep(sleep_s)
    out: list[TalkCandidate] = []
    for e in entries:
        c = _entry_to_candidate(e, conference=conference, discovery_method="channel")
        if c:
            out.append(c)
    return out


def discover_search(
    query: str,
    *,
    conference: Conference | None = None,
    max_results: int = 25,
    sleep_s: float = 0.8,
) -> list[TalkCandidate]:
    """YouTube search via yt-dlp ytsearchN:."""
    target = f"ytsearch{max_results}:{query}"
    entries = _run_yt_dlp(
        [
            "--flat-playlist",
            "-J",
            target,
        ],
        timeout=180,
    )
    time.sleep(sleep_s)
    out: list[TalkCandidate] = []
    for e in entries:
        c = _entry_to_candidate(e, conference=conference, discovery_method="search")
        if c:
            out.append(c)
    return out


def enrich_metadata(candidate: TalkCandidate, sleep_s: float = 0.3) -> TalkCandidate:
    """Fetch full metadata for a single video (description, date, etc.)."""
    entries = _run_yt_dlp(["-J", "--skip-download", candidate.url], timeout=90)
    time.sleep(sleep_s)
    if not entries:
        return candidate
    e = entries[0]
    enriched = _entry_to_candidate(
        e,
        conference=Conference(
            id=candidate.conference_id or "unknown",
            name=candidate.conference_name or "Unknown",
        )
        if candidate.conference_id
        else None,
        discovery_method=candidate.discovery_method,
    )
    if not enriched:
        return candidate
    # Preserve scoring fields if already set
    enriched.topics = candidate.topics
    enriched.score = candidate.score
    enriched.conference_id = candidate.conference_id or enriched.conference_id
    enriched.conference_name = candidate.conference_name or enriched.conference_name
    return enriched


def discover_for_conference(
    conference: Conference,
    *,
    years: Iterable[int],
    channel_limit: int = 60,
    search_per_query: int = 15,
    include_channels: bool = True,
    include_search: bool = True,
) -> list[TalkCandidate]:
    found: list[TalkCandidate] = []
    year_list = list(years)

    if include_channels:
        for handle in conference.youtube:
            try:
                found.extend(
                    discover_channel(handle, conference=conference, playlist_end=channel_limit)
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("channel discover failed %s: %s", handle, exc)

    if include_search:
        queries: list[str] = []
        for seed in conference.search:
            for y in year_list:
                queries.append(f"{seed} {y}")
            queries.append(seed)
        # Dedup while preserving order
        seen_q: set[str] = set()
        for q in queries:
            if q in seen_q:
                continue
            seen_q.add(q)
            try:
                found.extend(
                    discover_search(q, conference=conference, max_results=search_per_query)
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("search discover failed %r: %s", q, exc)

    # Dedup by video_id
    dedup: dict[str, TalkCandidate] = {}
    for c in found:
        if c.video_id not in dedup:
            dedup[c.video_id] = c
    return list(dedup.values())


def discover_topic_queries(
    queries: list[str],
    *,
    max_results: int = 30,
) -> list[TalkCandidate]:
    found: list[TalkCandidate] = []
    for q in queries:
        try:
            found.extend(discover_search(q, conference=None, max_results=max_results))
        except Exception as exc:  # noqa: BLE001
            log.warning("topic search failed %r: %s", q, exc)
    dedup: dict[str, TalkCandidate] = {}
    for c in found:
        if c.video_id not in dedup:
            dedup[c.video_id] = c
    return list(dedup.values())
