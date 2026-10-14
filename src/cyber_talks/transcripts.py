from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from cyber_talks.models import TranscriptSegment

log = logging.getLogger(__name__)


def _segments_to_text(segments: list[TranscriptSegment]) -> str:
    parts: list[str] = []
    for s in segments:
        t = (s.text or "").replace("\n", " ").strip()
        if t:
            parts.append(t)
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_vtt(content: str) -> list[TranscriptSegment]:
    """Minimal WebVTT parser → segments."""
    segments: list[TranscriptSegment] = []
    # Strip header / NOTE / STYLE blocks lightly
    lines = content.replace("\r\n", "\n").split("\n")
    i = 0
    time_re = re.compile(
        r"(?:(\d{2}):)?(\d{2}):(\d{2})\.(\d{3})\s-->\s(?:(\d{2}):)?(\d{2}):(\d{2})\.(\d{3})"
    )

    def to_seconds(h: str | None, m: str, s: str, ms: str) -> float:
        return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    while i < len(lines):
        line = lines[i].strip()
        m = time_re.search(line)
        if not m:
            i += 1
            continue
        start = to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
        end = to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
        i += 1
        text_parts: list[str] = []
        while i < len(lines) and lines[i].strip():
            # Remove VTT tags like <c>, <00:00:01.000>
            t = re.sub(r"<[^>]+>", "", lines[i]).strip()
            if t:
                text_parts.append(t)
            i += 1
        text = " ".join(text_parts)
        if text:
            segments.append(TranscriptSegment(start=start, duration=max(0.0, end - start), text=text))
    # Dedup consecutive identical caption rolls (auto-subs repeat)
    deduped: list[TranscriptSegment] = []
    prev = None
    for seg in segments:
        if prev is not None and seg.text == prev:
            continue
        deduped.append(seg)
        prev = seg.text
    return deduped


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=6), reraise=True)
def _fetch_via_api(video_id: str, languages: list[str]) -> tuple[str, str, list[TranscriptSegment]]:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )

    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound) as exc:
        raise RuntimeError(str(exc)) from exc

    fetched = None
    source = "manual"
    try:
        fetched = transcript_list.find_manually_created_transcript(languages)
        source = "manual"
    except Exception:  # noqa: BLE001
        try:
            fetched = transcript_list.find_generated_transcript(languages)
            source = "auto"
        except Exception:  # noqa: BLE001
            for t in transcript_list:
                fetched = t
                source = "manual" if not getattr(t, "is_generated", True) else "auto"
                break

    if fetched is None:
        raise RuntimeError("no transcript available")

    data = fetched.fetch()
    lang = getattr(fetched, "language_code", None) or (languages[0] if languages else "en")
    segments: list[TranscriptSegment] = []
    for item in data:
        if isinstance(item, dict):
            segments.append(
                TranscriptSegment(
                    start=float(item.get("start", 0)),
                    duration=float(item.get("duration", 0)),
                    text=str(item.get("text", "")),
                )
            )
        else:
            segments.append(
                TranscriptSegment(
                    start=float(getattr(item, "start", 0)),
                    duration=float(getattr(item, "duration", 0)),
                    text=str(getattr(item, "text", "")),
                )
            )
    return lang, source, segments


def _fetch_via_ytdlp(video_id: str, languages: list[str]) -> tuple[str, str, list[TranscriptSegment]]:
    """Fallback: download subs with yt-dlp (often works when the transcript API is IP-blocked)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    lang_pref = ",".join(languages)
    proxy = os.environ.get("YOUTUBE_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    with tempfile.TemporaryDirectory(prefix="cyber-talks-subs-") as tmp:
        outtmpl = str(Path(tmp) / f"{video_id}.%(ext)s")
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs",
            "--write-subs",
            "--sub-langs",
            lang_pref,
            "--sub-format",
            "vtt",
            "--no-warnings",
            "-o",
            outtmpl,
            url,
        ]
        if proxy:
            cmd[1:1] = ["--proxy", proxy]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        except FileNotFoundError as e:
            raise RuntimeError("yt-dlp not installed") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("yt-dlp subtitle download timed out") from e

        if proc.returncode not in (0, 1):
            raise RuntimeError(f"yt-dlp subs failed: {(proc.stderr or '')[:300]}")

        vtts = sorted(Path(tmp).glob(f"{video_id}*.vtt"))
        if not vtts:
            # Sometimes naming differs
            vtts = sorted(Path(tmp).glob("*.vtt"))
        if not vtts:
            raise RuntimeError("yt-dlp produced no VTT subtitles")

        # Prefer non-auto if both exist
        chosen = vtts[0]
        for p in vtts:
            name = p.name.lower()
            if ".en." in name or name.endswith(".en.vtt"):
                chosen = p
                break
        content = chosen.read_text(encoding="utf-8", errors="replace")
        segments = _parse_vtt(content)
        if not segments:
            raise RuntimeError("empty VTT after parse")
        source = "auto" if "auto" in chosen.name.lower() or "automatic" in content[:200].lower() else "ytdlp"
        # language from filename like id.en.vtt
        lang = "en"
        m = re.search(r"\.([a-z]{2}(?:-[A-Za-z]+)?)\.vtt$", chosen.name)
        if m:
            lang = m.group(1)
        return lang, source, segments


def fetch_transcript(
    video_id: str,
    *,
    languages: list[str] | None = None,
    sleep_s: float = 0.6,
    prefer_ytdlp: bool | None = None,
) -> dict[str, Any]:
    """
    Fetch transcript for a YouTube video.
    Tries youtube-transcript-api first (unless CYBER_TALKS_PREFER_YTDLP=1),
    then falls back to yt-dlp subtitle download.
    Optional: set YOUTUBE_PROXY / HTTPS_PROXY for cloud IP blocks.
    """
    langs = languages or ["en", "en-US", "en-GB"]
    if prefer_ytdlp is None:
        prefer_ytdlp = os.environ.get("CYBER_TALKS_PREFER_YTDLP", "").lower() in {"1", "true", "yes"}

    errors: list[str] = []
    order = ["ytdlp", "api"] if prefer_ytdlp else ["api", "ytdlp"]

    for method in order:
        try:
            if method == "api":
                lang, source, segments = _fetch_via_api(video_id, langs)
            else:
                lang, source, segments = _fetch_via_ytdlp(video_id, langs)
            time.sleep(sleep_s)
            return {
                "language": lang,
                "source": source,
                "text": _segments_to_text(segments),
                "segments": segments,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{method}: {exc}")
            log.info("transcript %s via %s failed: %s", video_id, method, str(exc)[:200])

    time.sleep(sleep_s)
    return {
        "language": None,
        "source": "none",
        "text": "",
        "segments": [],
        "error": " | ".join(errors)[:2000],
    }
