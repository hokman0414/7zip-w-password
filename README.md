# Cyber Talks Pipeline

Scrape **cybersecurity conference talks** from the last ~2 years (DEF CON, Black Hat, BSides, SANS, FIRST, HITB, and ~100 more), filter for **detection engineering**, **agentic/AI-SOC workflows**, **threat intelligence**, **insider threat**, and related technical topics, then pull **YouTube transcriptions** + speaker/channel attribution.

## What you get

| Output | Path |
|--------|------|
| Filtered talk list | `data/output/filtered_candidates.jsonl` |
| Per-talk JSON (metadata + attribution + transcript) | `data/output/talks/<video_id>.json` |
| Plaintext transcripts | `data/output/transcripts/<video_id>.txt` |
| Searchable index | `data/output/index.json` / `index.jsonl` |

## Quick start

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .

# See the ~100-conference registry
cyber-talks list-conferences

# Smoke test: a few big cons, then a handful of transcripts
cyber-talks run --max-conferences 5 --enrich-limit 40 --limit 20

# Best path for transcripts from cloud/datacenter IPs:
# AllBSides hosts captions on-page for thousands of BSides talks
cyber-talks allbsides --limit 100

# Full discover across the registry (slow; be polite to YouTube)
cyber-talks discover --years 2 --enrich-limit 300
cyber-talks transcribe --limit 200

cyber-talks stats
```

### Useful flags

- `--conference defcon --conference blackhat-usa` — limit to specific registry IDs  
- `--min-score 4` — stricter topic filter  
- `--discover-only` — skip caption fetch  
- `--skip-channels` — search-only discovery  

## How it works

1. **Registry** — `data/conferences/registry.json` lists ~100 conferences with YouTube handles + search seeds.  
2. **Discover** — `yt-dlp` lists channel uploads and runs `ytsearchN:` queries (plus optional [AllBSides](https://allbsides.com) scrape).  
3. **Filter** — `data/topics/keywords.yaml` scores titles/descriptions for detection eng, agentic workflows, CTI, insider threat, and general cyber technical terms.  
4. **Transcribe** — `youtube-transcript-api` pulls manual or auto captions.  
5. **Attribution** — channel, conference, upload date, heuristic speaker parse from title/description.

## Transcripts on cloud IPs

YouTube often blocks the caption API from datacenter IPs. The pipeline:

1. Tries `youtube-transcript-api`
2. Falls back to **`yt-dlp` subtitle download** (`--write-auto-subs`)

If both fail from your network:

```bash
export YOUTUBE_PROXY="http://user:pass@host:port"   # or HTTPS_PROXY
export CYBER_TALKS_PREFER_YTDLP=1                    # skip API, use yt-dlp first
cyber-talks transcribe --limit 50
```

Running on a residential/home IP usually works without a proxy.

## Legal / ethics

- Only public YouTube metadata and captions are used.  
- Respect [YouTube Terms](https://www.youtube.com/t/terms), conference copyrights, and speaker rights.  
- Default use case: **personal research**. Do not republish full transcripts unless you have rights.  
- The pipeline sleeps between requests; do not hammer APIs.

## Project layout

```
data/conferences/registry.json   # conference catalog
data/topics/keywords.yaml        # topic filters
src/cyber_talks/                 # discover / filter / transcript / CLI
tests/                           # unit tests for scoring + attribution
```

## Tests

```bash
python3 -m pip install -e .
python3 -m pytest tests/ -q
```
