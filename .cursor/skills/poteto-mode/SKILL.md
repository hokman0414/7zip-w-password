---
name: poteto-mode
description: >-
  Sticky router for this repo. Every trading request is parsed with the
  day-trader playbook and sized by the structured-analytic rules before any
  order is discussed. Use when the user talks about a trade, a trim, an exit,
  a buy, a review, or feedback from a fill.
---

# Potato mode

This mode stays on for trading requests. Read the playbook below as the steps, in order. Do not summarize them away.

The method is the day-trader skill at https://github.com/jakeschincariol/day-trader-skill adapted to this Robinhood book. Scanner, news, entry, exit, time machine, budget, risk, then the broker. The structured analysis decides the fraction. The broker step still needs the user's yes for that exact order.

## Playbook: a trading request

1. Take the user's words as the request. Run `silent-stocks parse-request` with those words and today's portfolio snapshot. The command writes `data/state/playbook_latest.json` and does not send an order.
2. Read `data/state/playbook_rules.json` before sizing. The fractions there are the current rules. The gaps are what the last fills taught.
3. For each named symbol, read the latest ACH leading hypothesis and red-team result. A failed thesis (red team defeated, H3, or H4), a leveraged fund, or a name with no structured report uses `trim_thesis_fails`. A thesis that still stands uses `trim_thesis_holds`. The word exit uses the exit fraction, which is the whole position up to the $400 order cap.
4. A name that is not held is a note, not an order. A review with no verb stronger than review is a note, not an order.
5. Risk gate, same idea as trader-risk. An order that only reduces shares already held can go through. An entry still has to be in `data/orders` for today with `armed` true. Do not edit `config/autotrade.json`, `silent_stocks/execution.py`, or `silent_stocks/portfolio_risk.py` to make an order fit.
6. Show each order on its own: symbol, side, shares, estimated dollars, the rule that set the fraction, and the quote disclosure. One yes covers one order. "Do trade" plus the named list is the yes for those orders and no others.
7. After a fill, record it with `silent-stocks record-executions`. On the next request, compare the fill price with the new price. A move of 5% or more updates the fraction by 0.25 and appends a gap. Exit stays at 1.0.

## What changed after 2026-11-20

BITU was an exit and the whole position sold. NBIS, CIFR, and IREN were red-team failures and were cut in half. DRAM had no company report and was also cut in half, so a named trim with no report is unconfirmed and uses that same half. A thesis that still stands trims a quarter. The next price after those fills moves the failed-thesis fraction.
