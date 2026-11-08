# Silent Stocks — STEMPLE multi-assignment research platform

Silent Stocks screens US-listed companies for under-followed fundamental improvement. It runs 100 isolated, evidence-cited
assignments per company and applies an 80/100 independent-evidence gate plus mandatory risk vetoes. It values each
company with bear/base/bull scenarios and a Monte Carlo, and it runs every weekday at 09:00 America/New_York.

It also assesses the connected Robinhood portfolio's risk and writes **trade proposals** (trims, hedges, buys). The Python
package never places orders; it contains no call to `place_equity_order`, and a test enforces that. Optional automated
execution is done by the daily agent skill (`.cursor/skills/silent-stocks-daily/`), which places only the orders that
`silent-stocks plan-orders` produced under hard guardrails. See [Automated daily execution](#automated-daily-execution).

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
| Automated order execution | Disarmed until the `ROBINHOOD_AGENTIC_ACCOUNT` secret is set (Cursor Dashboard → Cloud Agents → Secrets). Orders are placed by the agent through the Robinhood MCP, never by Python |

## Setup and commands

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
export SEC_USER_AGENT="Your Name you@example.com"

silent-stocks screen                     # SEC cross-sectional revenue-acceleration screen
silent-stocks analyze KTOS TWIN --verbose  # full report incl. all 100 votes
silent-stocks daily                      # one full daily run -> reports/briefs/<date>.md, DB, alerts, proposals, tracked-company trend
silent-stocks propose-trades             # portfolio risk + proposals as JSON (nothing submitted)
silent-stocks refresh-plan               # symbols, batches and date range the agent must snapshot today
silent-stocks validate-snapshot          # reconcile today's snapshots; exit 1 on errors
silent-stocks research-tasks             # tickers whose research is missing or older than 7 days
silent-stocks validate-research          # schema/source checks on data/research/agent_findings
silent-stocks plan-orders                # guarded order plan -> data/orders/<date>.json
silent-stocks record-executions FILE     # log placed orders -> data/executions/<date>.json, cooldown state
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
2. `silent-stocks schedule` (or cron calling `silent-stocks daily`) runs the pipeline each weekday at 09:00
   America/New_York. That run appends a price print for the disclosed public companies and writes
   `reports/trends/<date>.md`. A move of 5% or more from the prior print is an alert. It is not a research buy.
   Market data older than 96 hours marks a company `STALE DATA`, and research older than 30 days does too.
3. Review the brief. To act on a proposal manually, run its `review_equity_order` parameters in Robinhood and approve it
   yourself, or let the automated daily skill below execute the guarded plan.

## Automated daily execution

The daily skill (`.cursor/skills/silent-stocks-daily/SKILL.md`) is the full checklist an agent follows each weekday:
refresh snapshots through the Robinhood MCP, `validate-snapshot`, run deep-research subagents
(`silent_stocks/prompts/research_agent.md`) on the tickers from `research-tasks`, `validate-research`, `daily`,
`plan-orders`, then review and place exactly the planned orders (sells first, same `ref_id`), `record-executions`, and
commit the day's brief and state.

`plan-orders` only emits orders when every arming check passes; otherwise it lists `blocked_reasons` and shows
`would_place_if_armed`. Limits are in `config/autotrade.json` and are never loosened during a run.

| Guardrail | Setting |
|---|---|
| Arming | `enabled: true`, `ROBINHOOD_AGENTIC_ACCOUNT` set and ending in `account_last4`, no kill switch |
| Kill switch | `SILENT_STOP=1` or a file at `data/STOP_TRADING` |
| When | NYSE trading days only, 09:45–15:30 ET, snapshot at most 6 hours old and passing validation |
| Order kinds | risk trims, the `SH` hedge, QUALIFIED research buys, and the `SPY` core reinvest (capped at the fund limit) |
| Size | at most $400 per order, 20% of portfolio value per day, 6 orders per day, $5 minimum |
| Funding | buys only from settled cash/buying power above the 5% reserve; sell proceeds are used on the next run |
| Drawdown | buys halt at 15% below the high-water mark; everything halts at 30% |
| Churn | 3-day cooldown per symbol; quote drift above 5% from the plan price skips the order |
| Idempotency | deterministic `ref_id` per day/symbol/side/kind |

Vetoes only drive automatic trims when they come from the company's own filings or research and the company has complete
SEC fundamentals. Data-availability vetoes (ETFs, foreign filers) and vetoes on companies with incomplete history (recent
IPOs) are flagged `veto_needs_review` instead. The account number is read only from the environment; the plan uses the
placeholder `$ROBINHOOD_AGENTIC_ACCOUNT`, and `record-executions` refuses records that contain an account number.

To run it every weekday, create a Cursor Automation with a scheduled trigger at 09:45 America/New_York on weekdays,
select this repository and branch, enable the Robinhood MCP, and use the prompt
`Follow .cursor/skills/silent-stocks-daily/SKILL.md`. Automated trading can lose money; the guardrails limit how fast,
not whether.

## Statuses and gate

- **QUALIFIED**: exactly 100 assignments completed, at least 80 *independent* YES, bull case at least 2x, survives the red team, no critical veto.
- **UNDER REVIEW**: passes the vote gate but misses the 2x/red-team test, or has 65–79 independent YES.
- **DISCOVERY**: screened on filings and market data only, with no web research yet (research-dependent assignments abstain).
- **DISQUALIFIED**: has a critical veto, or the evidence is insufficient.
- **STALE DATA**: market or research inputs are too old.

YES votes whose supporting-evidence sets are identical are collapsed, so one fact cited by ten assignments counts once.
Critical vetoes:
- going-concern language
- cash runway under 12 months (only when operating cash flow is negative)
- dilution over 30% YoY (weighted diluted shares vs the split-restated year-ago quarter)
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

# Influence Intel: institution-level influence and sponsorship analysis

`influence_intel/` analyzes how a religious or civic organization sustains influence, using public records only, and
ranks where its sponsorship and advocacy are likely to go next. It works at the institution level: it never profiles
private individuals, members or individual donors (FEC disbursements to individuals are dropped at ingestion), and it
never infers anyone's religion or politics.

```
profile (EINs, LDA names, FEC committees) ─┐
Senate LDA lobbying filings ───────────────┤
ProPublica Form 990 financials ────────────┤                         ┌─> 13 influence pathways (explicit checks)
FEC committee disbursements (orgs only) ───┼─> cited evidence ───────┼─> STEMPLE (tailwind / headwind / mixed)
USAspending grants and contracts ──────────┤   (point-in-time)       ├─> ACH posture, key assumptions, red team,
congress.gov bill status ──────────────────┤                         │   premortem, signposts
GDELT news volume and tone ────────────────┤                         └─> next-sponsorship outlook (ranking index)
research subagent findings ────────────────┘
```

```bash
influence-intel find "Catholic Charities USA"     # candidate EINs, LDA client/registrant names, FEC committees
influence-intel analyze profiles/example_catholic_charities_usa.json   # -> reports/influence/<slug>/<date>.md/.json
influence-intel validate-research data/influence/research/<slug>.json
influence-intel demo                              # offline, synthetic, labeled DEMO
```

The agent skill `.cursor/skills/influence-intel/SKILL.md` runs the whole flow: build and verify the profile, launch
research subagents with `influence_intel/prompts/research_agent.md`, analyze, spot-check, and commit the brief.

How to read the output:

- **Pathways** (membership, trust, services, finances, government partnerships, lobbying, electoral, coalitions,
  legal, media, digital, transnational, property) are scored as the share of evaluated checks that pass. Checks
  without data are UNKNOWN and excluded; a pathway with fewer than two evaluated checks has no score. Exposure ranks
  weak or weakening pathways; the listed levers are lawful, transparent options to test, labeled as analyst judgment.
- **Outlook** scores (0-100) combine persistence, recency, momentum and independent corroboration of revealed
  behaviour. They rank continuity and are not probabilities. LDA filings do not say whether the organization supports
  or opposes a bill. Enacted bills, and pending companions folded into an enacted law, move to "lobbied bills that
  became law".
- **ACH** reports a tie rather than breaking it, and research evidence from one source domain counts once.
- **Hypotheses.** The brief also builds 1,000 hypotheses of the form "this subgroup supports this target through this
  pathway within this horizon", from the organization's own units (affiliates, lobbying registrants, researched
  subgroups). Nine diagnostics validate each one. A pathway scores only when the source records that kind of activity,
  so a lobbying filing supports a legislative hypothesis and not an unrelated one. The index ranks the hypotheses; it
  is not a probability. If the sourced evidence cannot fill 1,000, the brief says how many are real and does not invent
  the rest. The full set is in the JSON brief.

| Source | Needs |
|---|---|
| Senate LDA, ProPublica, USAspending, GDELT | Nothing (GDELT allows one request per 5 seconds and often rate-limits) |
| FEC, congress.gov | Work on the public `DEMO_KEY`; set `FEC_API_KEY` / `CONGRESS_API_KEY` (free api.data.gov keys) for volume |
| Research findings | An agent session with web access |

Limitations: churches and conventions of churches are exempt from LDA registration and from filing Form 990, so the
core body's activity can be invisible; only affiliates, hired firms and separately registered committees appear.
USAspending matches recipients by name and is labeled for verification. Bill supersession is matched by title.
