---
name: silent-stocks-daily
description: Daily Silent Stocks run. Refreshes Robinhood market and portfolio snapshots through the Robinhood MCP, runs deep-research subagents, runs the 100-assignment pipeline and portfolio risk checks, then executes only guardrail-approved risk-reducing trades on the agentic Robinhood account. Use for the scheduled weekday run or when asked to "run the daily stock checks".
---

# Silent Stocks daily run

Work from the repo root and run the steps in order. Use `.venv/bin/silent-stocks` if a venv exists; otherwise run
`python3 -m venv .venv && .venv/bin/pip install -q -e .` first. Times are America/New_York, and the schedule targets 09:45 ET on weekdays.

## Hard rules
- Only call `place_equity_order` for orders listed in `orders` of today's `data/orders/<date>.json`. Use exactly
  the params and `ref_id` given there. Never invent, enlarge, re-size or repeat an order. Never trade options, crypto,
  or symbols outside the plan.
- Never edit `config/autotrade.json`, `silent_stocks/execution.py` or `silent_stocks/portfolio_risk.py` during a run
  to loosen limits.
- If `plan-orders` reports `armed: false`, place nothing. Report the `blocked_reasons`.
- If any step fails or the data looks wrong, stop trading for the day and report what happened. Research and reports may still finish.
- The account number comes only from the `ROBINHOOD_AGENTIC_ACCOUNT` env var. Never write it to a file, commit or message.
- Mask account numbers as ••••last4 in any text.

## 1. Sync
`git pull --ff-only`. If `data/STOP_TRADING` exists, still do steps 2–4 but skip step 5.

## 2. Refresh Robinhood snapshots (read-only MCP calls)
1. Run `silent-stocks refresh-plan`. It prints the symbols in batches of 10 and the historicals parameters.
2. For each batch, call these Robinhood tools:
   - `get_equity_quotes(symbols)`
   - `get_equity_fundamentals(symbols)`
   - `get_equity_historicals(symbols, start_time, end_time, interval="month")` with the times from the plan.
3. Write `data/snapshots/robinhood/<YYYY-MM-DD>/market.json`:
   ```json
   {"source": "robinhood-mcp", "captured_at": "<UTC now>", "market_date": "<date>",
    "tools": ["get_equity_quotes", "get_equity_fundamentals", "get_equity_historicals(interval=month)"],
    "securities": {"SYM": {"company": "...", "price": 0.0, "price_time": "...Z", "market_cap": 0, "shares_outstanding": 0,
       "float": 0, "avg_volume_30d": 0, "high_52w": 0, "low_52w": 0, "pe_ratio": null, "pb_ratio": 0,
       "sector": "...", "industry": "...", "hq": "City, ST, US", "employees": 0, "listing_status": null,
       "price_12m_ago": 0.0, "monthly_closes": [12 closes oldest -> newest]}}}
   ```
   How to fill the fields:
   - `price`: whichever of `last_trade_price` / `last_non_reg_trade_price` has the newer timestamp. `price_time` is that timestamp.
   - `price_12m_ago`: the first month bar's `open_price`.
   - Drop bars with `interpolated: true`.
   - Store a negative P/E as null.
   - `listing_status`: Robinhood's `financial_status_description` when it isn't blank.
4. Get the account number from the `ROBINHOOD_AGENTIC_ACCOUNT` env var, then call these Robinhood tools on it:
   - `get_portfolio(account_number)`
   - `get_equity_positions(account_number)`
5. Write `data/snapshots/robinhood/<date>/portfolio.json`:
   ```json
   {"source": "robinhood-mcp", "captured_at": "<UTC now>", "positions": {
     "account_last4": "0643", "account_type": "limited_margin", "option_level": null,
     "portfolio": {"total_value": 0, "equity_value": 0, "crypto_value": 0, "cash": 0, "buying_power": 0},
     "benchmark": {"symbol": "SPY", "price": 0, "monthly_closes": [...]},
     "holdings": [{"symbol": "X", "quantity": 0, "available": 0, "price": 0, "monthly_closes": [...]}]}}
   ```
   How to fill the fields:
   - `available` is `shares_available_for_sells`.
   - `price` is the quote from step 3.
   - Copy `asset_type` and `leverage` tags for each symbol from the previous portfolio snapshot. Known tags: BITU is `leveraged_etf` with leverage 2.0, GLD is `commodity_etf`, EWY is `country_etf`. Add tags for new funds only when certain.
6. Run `silent-stocks validate-snapshot`. Fix every **error** by re-checking the MCP output; errors block trading.
   Read the warnings and fix any transcription mistakes they reveal.

## 3. Deep research (subagents)
1. Run `silent-stocks research-tasks --limit 12`. It returns tickers that have no research or research older than
   7 days, ordered holdings first, then the watchlist, then discoveries without critical vetoes.
2. Launch up to 4 `generalPurpose` subagents in parallel, each with up to 3 tickers. Give each one the full text of
   `silent_stocks/prompts/research_agent.md`, its tickers, and the output paths.
3. On Mondays, also launch one subagent to refresh `data/research/policy/policy_events.json` with the same
   sourcing rules. Keep the existing format: `{"researched_at", "agent_id", "events": [{"id", "country", "policy", "stage",
   "event_date", "expiration_date", "industries", "bottlenecks", "direction", "summary", "source_url", "source_title"}]}`.
   Cover the US, China, EU, Japan, South Korea, Taiwan, India, Canada, Australia and NATO.
4. Run `silent-stocks validate-research`, and fix or delete any invalid file.

## 4. Analysis
1. Run `silent-stocks daily`. It writes `reports/briefs/<date>.md` and `.json`, `data/state/*`, and today's proposals.
2. Read the brief.

## 5. Guarded execution
1. Run `silent-stocks plan-orders`, which writes `data/orders/<date>.json`.
   - If `armed` is false, skip to step 6.
2. For each entry in `orders`, sells first (the order they're listed in):
   1. Call `review_equity_order`. Use the entry's `params`, but replace `account_number` with `ROBINHOOD_AGENTIC_ACCOUNT`.
   2. Skip the order and record `skipped` with a reason when any of these happens:
      - the review returns any `order_checks` or alerts;
      - the quote moves more than `max_quote_drift_pct` from `ref_price`, when `ref_price` is set;
      - the instrument isn't active or tradable.
   3. Otherwise call `place_equity_order` with the same params and the entry's `ref_id`. Retry transient errors
      once, with the same `ref_id`.
   4. Append `{"ref_id", "symbol", "side", "kind", "status": "placed|skipped|failed", "reason", "order_id", "broker_state", "usd"}`
      to a list. Leave out the account number.
3. Write the list to `/tmp/executions.json`.
4. Run `silent-stocks record-executions /tmp/executions.json --total-value <portfolio total_value>`.

## 6. Commit and report
1. Commit `data/snapshots`, `data/research`, `data/state`, `data/orders`, `data/executions` and `reports/briefs`
   with the message `daily: <date>`, then push.
2. Reply with a short summary covering:
   - account value and portfolio beta;
   - orders placed, skipped and blocked, with reasons;
   - new alerts, including any tracked-company move of 5% or more;
   - the tracked-company trend (price, change versus the prior print, rising/falling/flat);
   - anything QUALIFIED or UNDER REVIEW;
   - data problems.

The refresh plan includes the disclosed public companies (GS, MMC, KR, FCF, WTFC, MCS, LUMI). Their prices are a trend log. A drastic move is not a research buy, and it is not added to the order plan.
