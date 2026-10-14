from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from cyber_talks.allbsides import discover_allbsides_sitemap, fetch_allbsides_talk, search_allbsides
from cyber_talks.attribution import build_attribution, extract_speakers
from cyber_talks.config import (
    ensure_output_dir,
    load_conferences,
    load_registry,
    load_topic_config,
)
from cyber_talks.discover import (
    discover_for_conference,
    discover_topic_queries,
    enrich_metadata,
)
from cyber_talks.filter import filter_candidates
from cyber_talks.models import SpeakerAttribution, TalkCandidate, TalkRecord
from cyber_talks.store import save_candidates, save_talk_record, write_index
from cyber_talks.transcripts import fetch_transcript

log = logging.getLogger(__name__)
console = Console()


def _since_years(years: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=int(365 * years))


def run_discover(
    *,
    out_dir: Path | None = None,
    years: float = 2.0,
    conference_ids: list[str] | None = None,
    max_conferences: int | None = None,
    channel_limit: int = 50,
    search_per_query: int = 12,
    skip_channels: bool = False,
    skip_search: bool = False,
    topic_searches: bool = True,
    allbsides: bool = True,
    min_score: float = 3.0,
    enrich: bool = True,
    enrich_limit: int | None = None,
) -> list[TalkCandidate]:
    out = ensure_output_dir(out_dir)
    registry = load_registry()
    conferences = load_conferences()
    topics = load_topic_config()
    since = _since_years(years)

    if conference_ids:
        wanted = set(conference_ids)
        conferences = [c for c in conferences if c.id in wanted]
    if max_conferences is not None:
        conferences = conferences[: max(0, max_conferences)]

    year_ints = sorted({datetime.now().year - i for i in range(int(years) + 1)})
    raw: list[TalkCandidate] = []

    console.print(f"[bold]Discovering talks[/] across {len(conferences)} conferences (since ~{since.date()})")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("conferences", total=len(conferences))
        for conf in conferences:
            progress.update(task, description=f"{conf.name}")
            try:
                found = discover_for_conference(
                    conf,
                    years=year_ints,
                    channel_limit=channel_limit,
                    search_per_query=search_per_query,
                    include_channels=not skip_channels,
                    include_search=not skip_search,
                )
                raw.extend(found)
                console.print(f"  {conf.id}: {len(found)} candidates")
            except Exception as exc:  # noqa: BLE001
                console.print(f"  [red]{conf.id} failed: {exc}[/]")
            progress.advance(task)

    if topic_searches:
        queries = list(registry.get("topic_search_queries", []))
        # Add year-scoped topic queries
        for q in list(queries):
            for y in year_ints:
                queries.append(f"{q} {y}")
        console.print(f"[bold]Topic searches[/]: {len(queries)} queries")
        raw.extend(discover_topic_queries(queries, max_results=20))

    if allbsides:
        console.print("[bold]AllBSides[/] topic scrapes + sitemap sample")
        for q in [
            "detection engineering",
            "threat intelligence",
            "insider threat",
            "threat hunting",
            "purple team",
            "agentic",
            "SIEM",
        ]:
            try:
                raw.extend(search_allbsides(q, limit=30))
            except Exception as exc:  # noqa: BLE001
                log.warning("allbsides %s: %s", q, exc)
        try:
            # Sitemap enumerates many BSides talks; titles filled during enrich/transcribe
            raw.extend(discover_allbsides_sitemap(limit=400))
        except Exception as exc:  # noqa: BLE001
            log.warning("allbsides sitemap: %s", exc)

    # Dedup before filter
    dedup: dict[str, TalkCandidate] = {}
    for c in raw:
        prev = dedup.get(c.video_id)
        if not prev or len(c.description) > len(prev.description):
            dedup[c.video_id] = c
    raw_list = list(dedup.values())
    save_candidates(out / "raw_candidates.jsonl", raw_list)
    console.print(f"Raw unique videos: {len(raw_list)}")

    # Optional enrich for better descriptions / dates (expensive)
    to_enrich = raw_list
    if enrich_limit is not None:
        to_enrich = raw_list[:enrich_limit]
    if enrich:
        console.print(f"[bold]Enriching metadata[/] for {len(to_enrich)} videos")
        enriched: list[TalkCandidate] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("enrich", total=len(to_enrich))
            for c in to_enrich:
                progress.update(task, description=c.video_id)
                try:
                    enriched.append(enrich_metadata(c))
                except Exception:  # noqa: BLE001
                    enriched.append(c)
                progress.advance(task)
        # Keep non-enriched remainder
        enriched_ids = {c.video_id for c in enriched}
        for c in raw_list:
            if c.video_id not in enriched_ids:
                enriched.append(c)
        raw_list = enriched

    filtered = filter_candidates(raw_list, topics, min_score=min_score, since=since)
    save_candidates(out / "filtered_candidates.jsonl", filtered)
    console.print(f"[green]Matched talks: {len(filtered)}[/] (min_score={min_score})")
    return filtered


def run_transcribe(
    candidates: list[TalkCandidate] | None = None,
    *,
    out_dir: Path | None = None,
    candidates_path: Path | None = None,
    limit: int | None = None,
    languages: list[str] | None = None,
) -> list[TalkRecord]:
    out = ensure_output_dir(out_dir)
    if candidates is None:
        import json

        path = candidates_path or (out / "filtered_candidates.jsonl")
        candidates = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    candidates.append(TalkCandidate.model_validate(json.loads(line)))

    if limit is not None:
        candidates = candidates[:limit]

    records: list[TalkRecord] = []
    console.print(f"[bold]Fetching transcripts[/] for {len(candidates)} talks")

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("transcripts", total=len(candidates))
        for c in candidates:
            progress.update(task, description=c.title[:50])
            speakers = extract_speakers(c)

            # Prefer AllBSides on-page transcript when available (works from cloud IPs)
            ab_url = (c.raw or {}).get("allbsides_url") or f"https://allbsides.com/talk/{c.video_id}.html"
            ab = fetch_allbsides_talk(ab_url)
            if ab.get("ok") and ab.get("title") and (
                c.title.startswith("AllBSides talk") or len(ab["title"]) > len(c.title)
            ):
                c.title = ab["title"]
            if ab.get("ok") and ab.get("description") and len(ab["description"]) > len(c.description or ""):
                c.description = ab["description"]
            if ab.get("ok") and ab.get("conference") and not c.conference_name:
                c.conference_name = ab["conference"]
                c.conference_id = c.conference_id or "media-allbsides"
            if ab.get("ok") and ab.get("upload_date") and not c.upload_date:
                c.upload_date = ab["upload_date"]
            if ab.get("ok") and ab.get("speakers"):
                for name in ab["speakers"]:
                    speakers.append(SpeakerAttribution(name=name, raw_credit="allbsides"))
                # dedup
                seen_n: set[str] = set()
                uniq: list[SpeakerAttribution] = []
                for s in speakers:
                    k = (s.name or "").lower()
                    if k and k not in seen_n:
                        seen_n.add(k)
                        uniq.append(s)
                speakers = uniq

            if ab.get("transcript_source") == "allbsides_page" and ab.get("transcript"):
                tr = {
                    "language": "en",
                    "source": "allbsides_page",
                    "text": ab["transcript"],
                    "segments": [],
                    "error": None,
                }
            else:
                tr = fetch_transcript(c.video_id, languages=languages)

            record = TalkRecord(
                video_id=c.video_id,
                title=c.title,
                url=c.url,
                description=c.description,
                channel=c.channel,
                channel_id=c.channel_id,
                upload_date=c.upload_date,
                duration_seconds=c.duration_seconds,
                view_count=c.view_count,
                conference_id=c.conference_id,
                conference_name=c.conference_name,
                discovery_method=c.discovery_method,
                topics=c.topics,
                score=c.score,
                speakers=speakers,
                transcript_language=tr.get("language"),
                transcript_source=tr.get("source"),
                transcript_text=tr.get("text") or "",
                transcript_segments=tr.get("segments") or [],
                attribution=build_attribution(c, speakers),
            )
            save_talk_record(out, record)
            records.append(record)
            progress.advance(task)

    write_index(out, records)
    with_tx = sum(1 for r in records if r.transcript_text)
    console.print(f"[green]Done[/]: {with_tx}/{len(records)} transcripts saved → {out}")
    return records


def run_pipeline(
    *,
    out_dir: Path | None = None,
    years: float = 2.0,
    conference_ids: list[str] | None = None,
    max_conferences: int | None = None,
    limit_transcripts: int | None = None,
    min_score: float = 3.0,
    enrich: bool = True,
    enrich_limit: int | None = 100,
    skip_channels: bool = False,
    dry_discover_only: bool = False,
) -> list[TalkRecord]:
    candidates = run_discover(
        out_dir=out_dir,
        years=years,
        conference_ids=conference_ids,
        max_conferences=max_conferences,
        min_score=min_score,
        enrich=enrich,
        enrich_limit=enrich_limit,
        skip_channels=skip_channels,
    )
    if dry_discover_only:
        return []
    return run_transcribe(candidates, out_dir=out_dir, limit=limit_transcripts)
