from __future__ import annotations

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from cyber_talks.config import OUTPUT_DIR, load_conferences, load_registry
from cyber_talks.pipeline import run_discover, run_pipeline, run_transcribe

console = Console()


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Scrape cyber conference talks + YouTube transcripts (detection eng, TI, agentic, …)."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    _setup_logging(verbose)


@main.command("list-conferences")
def list_conferences() -> None:
    """Show the conference registry."""
    confs = load_conferences()
    table = Table(title=f"Conferences ({len(confs)})")
    table.add_column("id")
    table.add_column("name")
    table.add_column("country")
    table.add_column("youtube")
    for c in confs:
        table.add_row(c.id, c.name, c.country, ", ".join(c.youtube) or "—")
    console.print(table)


@main.command("discover")
@click.option("--years", default=2.0, show_default=True, help="Look back N years")
@click.option("--conference", "conference_ids", multiple=True, help="Limit to conference id(s)")
@click.option("--max-conferences", type=int, default=None, help="Cap number of conferences")
@click.option("--min-score", default=3.0, show_default=True)
@click.option("--no-enrich", is_flag=True, help="Skip per-video metadata enrich")
@click.option("--enrich-limit", type=int, default=150, show_default=True)
@click.option("--skip-channels", is_flag=True)
@click.option("--out", type=click.Path(path_type=Path), default=None)
def discover_cmd(
    years: float,
    conference_ids: tuple[str, ...],
    max_conferences: int | None,
    min_score: float,
    no_enrich: bool,
    enrich_limit: int,
    skip_channels: bool,
    out: Path | None,
) -> None:
    """Discover + filter talks (writes filtered_candidates.jsonl)."""
    run_discover(
        out_dir=out or OUTPUT_DIR,
        years=years,
        conference_ids=list(conference_ids) or None,
        max_conferences=max_conferences,
        min_score=min_score,
        enrich=not no_enrich,
        enrich_limit=enrich_limit,
        skip_channels=skip_channels,
    )


@main.command("transcribe")
@click.option("--limit", type=int, default=None, help="Max talks to transcribe")
@click.option(
    "--from-file",
    type=click.Path(path_type=Path, exists=True),
    default=None,
    help="JSONL candidates file",
)
@click.option("--out", type=click.Path(path_type=Path), default=None)
@click.option("--lang", multiple=True, default=["en", "en-US"], show_default=True)
def transcribe_cmd(
    limit: int | None,
    from_file: Path | None,
    out: Path | None,
    lang: tuple[str, ...],
) -> None:
    """Fetch YouTube captions for filtered candidates."""
    run_transcribe(
        out_dir=out or OUTPUT_DIR,
        candidates_path=from_file,
        limit=limit,
        languages=list(lang),
    )


@main.command("run")
@click.option("--years", default=2.0, show_default=True)
@click.option("--conference", "conference_ids", multiple=True)
@click.option("--max-conferences", type=int, default=None)
@click.option("--limit", "limit_transcripts", type=int, default=None, help="Cap transcript fetches")
@click.option("--min-score", default=3.0, show_default=True)
@click.option("--no-enrich", is_flag=True)
@click.option("--enrich-limit", type=int, default=100, show_default=True)
@click.option("--skip-channels", is_flag=True)
@click.option("--discover-only", is_flag=True)
@click.option("--out", type=click.Path(path_type=Path), default=None)
def run_cmd(
    years: float,
    conference_ids: tuple[str, ...],
    max_conferences: int | None,
    limit_transcripts: int | None,
    min_score: float,
    no_enrich: bool,
    enrich_limit: int,
    skip_channels: bool,
    discover_only: bool,
    out: Path | None,
) -> None:
    """Full pipeline: discover → filter → transcribe."""
    run_pipeline(
        out_dir=out or OUTPUT_DIR,
        years=years,
        conference_ids=list(conference_ids) or None,
        max_conferences=max_conferences,
        limit_transcripts=limit_transcripts,
        min_score=min_score,
        enrich=not no_enrich,
        enrich_limit=enrich_limit,
        skip_channels=skip_channels,
        dry_discover_only=discover_only,
    )


@main.command("allbsides")
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--min-score", default=3.0, show_default=True)
@click.option("--out", type=click.Path(path_type=Path), default=None)
@click.option("--years", default=2.0, show_default=True)
def allbsides_cmd(limit: int, min_score: float, out: Path | None, years: float) -> None:
    """Bulk scrape AllBSides talk pages (includes on-page transcripts)."""
    import json
    from datetime import datetime, timedelta, timezone

    from cyber_talks.allbsides import discover_allbsides_sitemap, fetch_allbsides_talk
    from cyber_talks.config import ensure_output_dir, load_topic_config
    from cyber_talks.filter import filter_candidates
    from cyber_talks.models import SpeakerAttribution, TalkCandidate, TalkRecord
    from cyber_talks.attribution import build_attribution, extract_speakers
    from cyber_talks.store import save_candidates, save_talk_record, write_index

    from cyber_talks.allbsides import (
        _extract_youtube_id,
        list_talk_urls_from_sitemap,
        search_allbsides,
    )
    from cyber_talks.filter import score_talk

    out_dir = ensure_output_dir(out or OUTPUT_DIR)
    topics = load_topic_config()
    since = datetime.now(timezone.utc) - timedelta(days=int(365 * years))

    # Seed with topic searches (higher hit rate than raw sitemap order)
    seed: list[TalkCandidate] = []
    for q in [
        "detection engineering",
        "threat hunting",
        "threat intelligence",
        "insider threat",
        "purple team",
        "sigma",
        "SIEM",
        "agentic",
        "LLM",
        "attribution",
    ]:
        seed.extend(search_allbsides(q, limit=40))

    # Also walk sitemap until we have enough scored matches
    sitemap_urls = list_talk_urls_from_sitemap(limit=None)
    console.print(
        f"[bold]AllBSides[/]: {len(seed)} search hits, {len(sitemap_urls)} sitemap URLs — "
        f"collecting {limit} topic-matched talks"
    )

    seen: set[str] = set()
    kept: list[TalkCandidate] = []
    scanned = 0
    max_scan = max(limit * 25, 400)

    def consider(video_id: str, hint: TalkCandidate | None = None) -> None:
        nonlocal scanned
        if video_id in seen or len(kept) >= limit:
            return
        seen.add(video_id)
        scanned += 1
        ab = fetch_allbsides_talk(video_id)
        if not ab.get("ok"):
            return
        c = hint or TalkCandidate(
            video_id=video_id,
            title=ab.get("title") or video_id,
            url=f"https://www.youtube.com/watch?v={video_id}",
            discovery_method="allbsides",
            conference_id="media-allbsides",
            conference_name="AllBSides aggregator",
        )
        c.title = ab.get("title") or c.title
        c.description = ab.get("description") or c.description
        c.conference_name = ab.get("conference") or c.conference_name
        c.upload_date = ab.get("upload_date") or c.upload_date
        c.channel = c.channel or "AllBSides"
        c.raw = {
            **(c.raw or {}),
            "allbsides_url": ab.get("url"),
            "allbsides_transcript": ab.get("transcript") or "",
            "allbsides_speakers": ab.get("speakers") or [],
        }
        scored = score_talk(c, topics, min_score=min_score, since=None)
        if not scored:
            return
        dt = scored.upload_datetime
        if dt and dt.replace(tzinfo=timezone.utc) < since:
            return
        kept.append(scored)

    for c in seed:
        consider(c.video_id, c)
        if len(kept) >= limit:
            break

    if len(kept) < limit:
        for u in sitemap_urls:
            vid = _extract_youtube_id(u)
            if not vid:
                continue
            consider(vid)
            if len(kept) >= limit or scanned >= max_scan:
                break

    console.print(f"Matched {len(kept)} talks after scanning {scanned} pages")
    save_candidates(out_dir / "filtered_candidates.jsonl", kept)

    records: list[TalkRecord] = []
    for c in kept:
        speakers = extract_speakers(c)
        for name in (c.raw or {}).get("allbsides_speakers") or []:
            speakers.append(SpeakerAttribution(name=name, raw_credit="allbsides"))
        tx = (c.raw or {}).get("allbsides_transcript") or ""
        if not tx:
            ab = fetch_allbsides_talk(c.video_id)
            tx = ab.get("transcript") or ""
            for name in ab.get("speakers") or []:
                speakers.append(SpeakerAttribution(name=name, raw_credit="allbsides"))
        record = TalkRecord(
            video_id=c.video_id,
            title=c.title,
            url=c.url,
            description=c.description,
            channel=c.channel,
            upload_date=c.upload_date,
            conference_id=c.conference_id,
            conference_name=c.conference_name,
            discovery_method=c.discovery_method,
            topics=c.topics,
            score=c.score,
            speakers=speakers,
            transcript_language="en" if tx else None,
            transcript_source="allbsides_page" if tx else "none",
            transcript_text=tx,
            attribution=build_attribution(c, speakers),
        )
        save_talk_record(out_dir, record)
        records.append(record)
    write_index(out_dir, records)
    with_tx = sum(1 for r in records if r.transcript_text)
    console.print(f"[green]AllBSides done[/]: {with_tx}/{len(records)} transcripts → {out_dir}")


@main.command("stats")
@click.option("--out", type=click.Path(path_type=Path), default=None)
def stats_cmd(out: Path | None) -> None:
    """Summarize scraped output."""
    import json

    out_dir = out or OUTPUT_DIR
    index = out_dir / "index.json"
    filtered = out_dir / "filtered_candidates.jsonl"
    reg = load_registry()
    console.print(f"Registry conferences: {len(reg.get('conferences', []))}")
    if filtered.exists():
        n = sum(1 for _ in filtered.open() if _.strip())
        console.print(f"Filtered candidates: {n}")
    if index.exists():
        data = json.loads(index.read_text())
        with_tx = sum(1 for r in data if r.get("transcript_chars", 0) > 0)
        console.print(f"Indexed talks: {len(data)} ({with_tx} with transcripts)")
        by_topic: dict[str, int] = {}
        for r in data:
            for t in r.get("topics") or []:
                by_topic[t] = by_topic.get(t, 0) + 1
        if by_topic:
            table = Table(title="Topics")
            table.add_column("topic")
            table.add_column("count", justify="right")
            for t, c in sorted(by_topic.items(), key=lambda x: -x[1]):
                table.add_row(t, str(c))
            console.print(table)
    else:
        console.print("No index yet — run discover/transcribe first.")


if __name__ == "__main__":
    main()
