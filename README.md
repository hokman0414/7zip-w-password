# Silent Stocks — STEMPLE multi-assignment research platform

Silent Stocks screens US-listed companies for under-followed fundamental improvement. It runs 100 isolated, evidence-cited
assignments per company and applies an 80/100 independent-evidence gate plus mandatory risk vetoes. It values each
company with bear/base/bull scenarios and a Monte Carlo, and it runs every weekday at 09:00 America/New_York.

It also assesses the connected Robinhood portfolio's risk and writes **trade proposals** (trims, hedges, buys). **It never
places orders.** Each proposal carries the exact `review_equity_order` parameters so a person can review and approve
it in Robinhood. The package contains no call to `place_equity_order`, and a test enforces that.

> A vote count of 80/100 is a research evidence threshold. It is **not** an 80% probability that a stock doubles.
> UNKNOWN votes and abstentions never count as YES. Output is research, not investment advice.

## Pipeline

```
SEC frames screen ─┐
watchlist ─────────┼─> evidence collection ─> STEMPLE + policy graph ─> 100 assignments ─> tally (duplicate-evidence
Robinhood snapshot ┘   (XBRL, filings, FTS,                              (isolated slices)   collapse) + risk vetoes
research findings      USAspending, findings)                                                       │
                                                                                                     v
            brief / DB / API / dashboard <─ status <─ structured analytic techniques <─ valuation + Monte Carlo
                       │
                       └─> portfolio risk (weights, vol, beta, clusters) ─> PROPOSED trims / hedge / buys (human approval)
```

| Module | Role |
|---|---|
| `connectors/sec_edgar.py` | Ticker map, XBRL company facts, cross-sectional frames, submissions, full-text search |
| `connectors/usaspending.py` | Federal contract awards, name-matched and labeled "verify recipient" |
| `connectors/market.py` | Robinhood MCP snapshot reader (timestamps preserved) and a Polygon production connector |
| `connectors/research.py` | Pydantic-validated web-research findings and international policy events |
| `financials.py` | Point-in-time fundamentals (only facts filed on or before `as_of`) with quarter reconstruction |
| `discovery.py` | Revenue-acceleration screen plus the Silent Stock Discovery Score (attention, catalysts, valuation, fundamentals) |
| `assignments.py` | The 100 assignments: 15 macro/policy, 15 company financial, 15 technology/competitive, 15 valuation, 10 military/geopolitical, 10 supply chain, 10 risk/forensic, 10 catalyst/alternative |
| `context.py` | `SliceView`: each assignment can read only the evidence slices it declares |
| `voting.py` | Execution log, tally, evidence-dependency collapse, vetoes, status |
| `valuation.py` | EV, multiples, revenue needed to double, scenarios, sensitivity grid, Monte Carlo (seeded) |
| `stemple.py`, `policy_graph.py`, `sat.py` | STEMPLE assessments, Country→Policy→Industry→Bottleneck→Company graph, and the structured analytic techniques: ACH, key assumptions, signposts, red team, devil's advocacy, premortem, scenarios, cross-impact, Bayesian (calibrated inputs only), Monte Carlo |
| `portfolio_risk.py` | Portfolio beta/vol (Blume-adjusted), concentration, leverage, correlated clusters, proposals |
| `daily.py`, `scheduler.py` | Daily run, alert dedupe by state hash, markdown/JSON brief, APScheduler cron |
| `db.py`, `api.py`, `dashboard.py`, `cli.py` | SQLite store, read-only FastAPI, Streamlit dashboard, CLI |
| `llm.py` | Optional LLM reviewer for assignments. A YES must cite evidence ids that exist in the assignment's slice |
| `demo.py` | Offline demo built on labeled, synthetic fixtures |

## What works and what needs credentials

| Component | Status |
|---|---|
| SEC EDGAR (XBRL, frames, submissions, full-text search) | Works, no key. Set `SEC_USER_AGENT="Your Name you@example.com"` as SEC requires |
| USAspending awards | Works, no key |
| Robinhood market data and portfolio | Works through the Robinhood MCP in an agent session, which writes JSON snapshots to `data/snapshots/robinhood/<date>/`. Python cannot call the MCP directly |
| Web research findings and policy events | Collected by research subagents with source URLs into `data/research/`. Refreshing them requires an agent session |
| Polygon market data (alternative to snapshots) | Needs `POLYGON_API_KEY` |
| LLM assignment reviewer | Needs `OPENAI_API_KEY` and `SILENT_LLM_MODEL`. Without them every assignment is labeled `executor=rule-based` |
| Analyst coverage, 13F institutional ownership | Not configured. Listed as missing in the discovery score, never imputed |
| Bayesian updating | Not applied until `data/calibration/base_rates.json` exists (point-in-time backtest base rates) |
| Order execution | Not implemented, on purpose |

## Setup and commands

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
export SEC_USER_AGENT="Your Name you@example.com"

silent-stocks screen                     # SEC cross-sectional revenue-acceleration screen
silent-stocks analyze KTOS TWIN --verbose  # full report incl. all 100 votes
silent-stocks daily                      # one full daily run -> reports/briefs/<date>.md, DB, alerts, proposals
silent-stocks propose-trades             # portfolio risk + proposals as JSON (nothing submitted)
silent-stocks schedule                   # weekdays 09:00 America/New_York
silent-stocks api                        # http://127.0.0.1:8000/companies, /alerts, /proposals
silent-stocks dashboard                  # Streamlit on :8501
silent-stocks demo                       # offline fixture demo, labeled DEMO
pytest
```

### Daily refresh workflow

1. Before 09:00 ET, an MCP-capable agent session refreshes the Robinhood snapshots. It calls `get_equity_quotes`,
   `get_equity_fundamentals`, `get_equity_historicals(interval=month)` and `get_portfolio`/`get_equity_positions`, then
   writes them under `data/snapshots/robinhood/<date>/`. The research subagents refresh `data/research/`.
2. `silent-stocks schedule` (or cron calling `silent-stocks daily`) runs the pipeline. Market data older than 96 hours
   marks a company `STALE DATA`, and research older than 30 days does too.
3. Review the brief. To act on a proposal, run its `review_equity_order` parameters in Robinhood and approve it yourself.

## Statuses and gate

- **QUALIFIED**: exactly 100 assignments completed, at least 80 *independent* YES, bull case at least 2x, survives the red team, no critical veto.
- **UNDER REVIEW**: passes the vote gate but misses the 2x/red-team test, or has 65–79 independent YES.
- **DISCOVERY**: screened on filings and market data only, with no web research yet (research-dependent assignments abstain).
- **DISQUALIFIED**: has a critical veto, or the evidence is insufficient.
- **STALE DATA**: market or research inputs are too old.

YES votes whose supporting-evidence sets are identical are collapsed, so one fact cited by ten assignments counts once.
Critical vetoes:
- going-concern language
- cash runway under 12 months
- dilution over 30% YoY
- negative equity
- exchange noncompliance
- price under $1
- restatement (8-K Item 4.02)
- critical research risk
- missing fundamentals or market data
- stale data

Material weakness and a 12-month move above 150% are warnings only.

## Proposal rules (`RiskLimits`)

| Rule | Limit |
|---|---|
| Single stock weight | 10%, trimmed to 8% |
| Fund weight (commodity, country or index ETF) | 20%, trimmed to 18% |
| Leveraged ETF weight | 3% |
| High-volatility names (realized vol above 80%) | 4% |
| Holdings with a critical research veto | 1% |
| Target portfolio beta | 1.0 ± 0.15 |
| Cash reserve | 5% |

If beta is still above target after trims, the hedge is an inverse S&P ETF (`SH`), because the account has no
options level. It is funded only from trim proceeds above the cash reserve. A new buy requires a QUALIFIED company and
is capped at 4% as a starter position.

## Known limitations

- Rule-based assignments are deterministic checks over the evidence. They are not independent agents with judgment.
- Name-matched USAspending awards can include a different recipient with a similar name. Each one is labeled for verification.
- Full-text search for "substantial doubt … going concern" can match risk-factor boilerplate. Hits link to the filing for review.
- Peer medians come from the analyzed set, grouped by Robinhood sector. The sets are coarse, so the re-rating is capped at 0.5x–2x of the current multiple.
- Scenario probabilities are not calibrated and are left unassigned. The Monte Carlo output is model-implied, not a probability of an outcome.
