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

The method is the day-trader skill at https://github.com/jakeschincariol/day-trader-skill adapted to this Robinhood book. Scanner, news, entry, exit, time machine, budget, risk, then the broker. The structured analysis decides the fraction. Starting 2026-11-23, the words "do trade" are the yes for the whole plan, buys and sells.

## Playbook: a trading request

1. Take the user's words as the request. Run `silent-stocks parse-request` with those words and today's portfolio snapshot. The command writes `data/state/playbook_latest.json` and does not send an order.
2. Read `data/state/playbook_rules.json` before sizing. The fractions there are the current rules. The gaps are what the last fills taught.
3. For each named symbol, read the latest ACH leading hypothesis and red-team result. A failed thesis (red team defeated, H3, or H4), a leveraged fund, or a name with no structured report uses `trim_thesis_fails`. A thesis that still stands uses `trim_thesis_holds`. The word exit uses the exit fraction, which is the whole position up to the $400 order cap.
4. A name that is not held is a note, not an order. A review with no verb stronger than review is a note, not an order.
5. Risk gate, same idea as trader-risk. An order that only reduces shares already held can go through. An entry has to be in today's plan. Do not edit `config/autotrade.json`, `silent_stocks/execution.py`, or `silent_stocks/portfolio_risk.py` to make an order fit.
6. "Do trade" means run the daily checklist straight through and place the plan, buys and sells. Do not pause between steps and do not repeat a rejected order later the same day. If the plan is disarmed only because the account variable is unset, place `would_place_if_armed`. Review each order first. Skip one order when the broker returns a check, the quote drifts more than 5%, or the market is closed. Then report each fill: symbol, side, shares, dollars, the rule, and the quote disclosure.
7. After a fill, record it with `silent-stocks record-executions`, including `fill_price` and `filled_at`. Score a batch of fills (one rule, one fill day) with `learn_from_fills` once, after 3 trading sessions, against the regular-session price. Before that, a move is a note. The shared fraction moves by 0.25 only when the median move of that setup is 5% or more. One name does not swing the rule. A closed-market overnight print is a note. Exit stays at 1.0.
8. When the user asks why the account is losing money, split the loss three ways before changing a rule:
   - the market (account change versus SPY over the same dates);
   - entries made before the system (average cost versus price);
   - what the system did (each sale's price versus the price now, and each buy's fill versus the price now).
   Change a rule only for the third part.

## What changed after 2026-11-20

BITU was an exit and the whole position sold. NBIS, CIFR, and IREN were red-team failures and were cut in half. DRAM had no company report and was also cut in half, so a named trim with no report is unconfirmed and uses that same half. A thesis that still stands trims a quarter.

## What changed on 2026-11-25

On 2026-11-23, one session after the Friday trims, they were up a median 15%, and the failed-thesis fraction stepped from 0.50 to 0.25. By the third session they were a median 3.7% below the fill prices. The step was undone, and a batch is now scored once, after 3 sessions. Every sale from 2026-11-12 to 2026-11-20 was followed by a further fall. Holding those shares would have cost $239 more, so the sells were not the leak. The account fell about as much as SPY did. The one loss the system caused was the 2026-11-23 SPY core buy, made while SPY was below its 10-month average. The core reinvest now pauses below that average.
