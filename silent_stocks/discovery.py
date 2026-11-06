"""Silent Stock discovery.

Stage 1 (universe screen) uses SEC XBRL *frames*: one call returns a concept for every filer for a calendar quarter,
so the screen covers all exchange-listed SEC filers rather than a watchlist. It ranks fundamental improvement
(revenue growth, acceleration, gross-margin trend).

Stage 2 (Silent Stock Discovery Score) adds attention, valuation and catalyst proxies once market data and
research evidence exist. Missing components are labeled and excluded from the weighting, never imputed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from math import log10

from .connectors.sec_edgar import LISTED_EXCHANGES, SecEdgar

REVENUE_FRAME_CONCEPTS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]


def latest_reported_quarter(as_of: date, lag_days: int = 50) -> tuple[int, int]:
    """Most recent calendar quarter whose 10-Qs are broadly filed by `as_of` (point-in-time safe)."""
    y, q = as_of.year, (as_of.month - 1) // 3 + 1
    for _ in range(8):
        q -= 1
        if q == 0:
            y, q = y - 1, 4
        end_month = q * 3
        end = date(y, end_month, 30 if end_month in (6, 9) else 31)
        if (as_of - end).days >= lag_days:
            return y, q
    raise ValueError("no reported quarter")


def _shift(y: int, q: int, n: int) -> tuple[int, int]:
    idx = y * 4 + (q - 1) + n
    return idx // 4, idx % 4 + 1


@dataclass
class ScreenRow:
    ticker: str
    cik: int
    name: str
    exchange: str | None
    revenue_q: float
    revenue_q_prior_year: float
    growth_yoy: float
    growth_yoy_prev_q: float | None
    acceleration: float | None
    gross_margin: float | None
    gross_margin_prior_year: float | None
    fundamental_score: float
    period: str
    sources: list[str] = field(default_factory=list)
    sic: str | None = None
    sic_description: str | None = None
    state_of_incorporation: str | None = None


def _frame_map(sec: SecEdgar, concept_list: list[str], period: str) -> tuple[dict[int, dict], list[str]]:
    out: dict[int, dict] = {}
    urls = []
    for concept in concept_list:
        rows, prov = sec.frame(concept, period)
        urls.append(prov.get("url", ""))
        for r in rows:
            out.setdefault(int(r["cik"]), r)
    return out, urls


EXCLUDED_SIC = {"2834", "2836", "6770", "6798", "8731"}


def sic_excluded(sic: str | None) -> bool:
    """Pharma/biotech, blank checks, REITs, R&D labs and the finance division (60xx-67xx) are out of scope."""
    if not sic:
        return False
    return sic in EXCLUDED_SIC or sic.startswith(("60", "61", "62", "63", "64", "65", "67"))


def enrich_and_filter(sec: SecEdgar, rows: list["ScreenRow"], limit: int = 60) -> list["ScreenRow"]:
    kept = []
    for r in rows:
        try:
            sub, _ = sec.submissions(r.cik)
        except Exception:  # noqa: BLE001 - unreachable metadata keeps the row, labeled
            r.sic, r.sic_description = None, "unknown (submissions unavailable)"
            kept.append(r)
            continue
        r.sic, r.sic_description = sub.get("sic"), sub.get("sicDescription")
        r.state_of_incorporation = sub.get("stateOfIncorporation")
        if not sic_excluded(r.sic):
            kept.append(r)
        if len(kept) >= limit:
            break
    return kept


def screen_universe(sec: SecEdgar, as_of: date, min_revenue_q: float = 5e6, min_growth: float = 0.20,
                    max_revenue_q: float = 1.5e9, max_growth: float = 4.0, require_persistent: bool = True,
                    require_gross_profit: bool = True) -> list[ScreenRow]:
    y, q = latest_reported_quarter(as_of)
    periods = {k: f"CY{yy}Q{qq}" for k, (yy, qq) in {
        "cur": (y, q), "prior": _shift(y, q, -4), "prev": _shift(y, q, -1), "prev_prior": _shift(y, q, -5)}.items()}
    frames, sources = {}, []
    for k, p in periods.items():
        frames[k], urls = _frame_map(sec, REVENUE_FRAME_CONCEPTS, p)
        sources += urls
    gp_cur, u1 = _frame_map(sec, ["GrossProfit"], periods["cur"])
    gp_prior, u2 = _frame_map(sec, ["GrossProfit"], periods["prior"])
    sources += u1 + u2
    by_cik = {}
    for lst in sec.listings().values():
        if lst.exchange in LISTED_EXCHANGES:
            by_cik.setdefault(lst.cik, lst)
    rows: list[ScreenRow] = []
    for cik, cur in frames["cur"].items():
        listing = by_cik.get(cik)
        prior = frames["prior"].get(cik)
        if not listing or not prior:
            continue
        rev, rev_p = float(cur["val"]), float(prior["val"])
        if rev < min_revenue_q or rev > max_revenue_q or rev_p <= 0:
            continue
        g = rev / rev_p - 1
        # >400% YoY is usually acquisitions, milestone revenue or a tiny base: not comparable organic growth.
        if g < min_growth or g > max_growth:
            continue
        prev, prev_p = frames["prev"].get(cik), frames["prev_prior"].get(cik)
        g_prev = float(prev["val"]) / float(prev_p["val"]) - 1 if prev and prev_p and float(prev_p["val"]) > 0 else None
        if require_persistent and (g_prev is None or g_prev < 0.05):
            continue
        accel = g - g_prev if g_prev is not None else None
        gm = float(gp_cur[cik]["val"]) / rev if cik in gp_cur else None
        gm_p = float(gp_prior[cik]["val"]) / rev_p if cik in gp_prior else None
        # Operating businesses with a cost of goods: excludes most biotech royalty, REIT and financial revenue.
        if require_gross_profit and (gm is None or gm_p is None or gm <= 0):
            continue
        # Bounded components so one extreme value (e.g. a tiny base) cannot dominate.
        score = min(g, 1.5) / 1.5 * 50
        score += (max(min(accel, 0.5), -0.5) + 0.5) * 30 if accel is not None else 15
        score += 20 if (gm is not None and gm_p is not None and gm > gm_p) else 0
        rows.append(ScreenRow(listing.ticker, cik, listing.name, listing.exchange, rev, rev_p, g, g_prev, accel,
                              gm, gm_p, round(score, 2), periods["cur"], sources=[s for s in sources if s]))
    return sorted(rows, key=lambda r: r.fundamental_score, reverse=True)


@dataclass
class DiscoveryScore:
    score: float | None
    components: dict
    missing: list[str]
    label: str = ("Silent Stock Discovery Score ranks relative attention, catalysts, valuation and fundamental "
                  "improvement. Low attention is NOT evidence of undervaluation.")


def discovery_score(*, market_cap: float | None, turnover_daily: float | None, return_12m: float | None,
                    pct_below_52w_high: float | None, ev_revenue: float | None, revenue_growth: float | None,
                    acceleration: float | None, margin_change: float | None, fcf_change_positive: bool | None,
                    dated_catalysts_3_12m: int | None, gov_award_value_to_revenue: float | None,
                    verified_policy_links: int | None, news_items_90d: int | None) -> DiscoveryScore:
    comps: dict[str, float] = {}
    missing: list[str] = []

    def put(name: str, value: float | None, weight: float):
        if value is None:
            missing.append(name)
        else:
            comps[name] = (max(0.0, min(1.0, value)), weight)

    put("attention:size", None if not market_cap else 1 - (log10(market_cap) - 7.5) / 3.0, 8)
    put("attention:turnover", None if turnover_daily is None else 1 - min(turnover_daily / 0.03, 1), 8)
    put("attention:news_frequency", None if news_items_90d is None else 1 - min(news_items_90d / 30, 1), 4)
    missing.append("attention:analyst_coverage (no licensed source configured)")
    missing.append("attention:institutional_ownership (no 13F aggregation configured)")
    put("fundamental:revenue_growth", None if revenue_growth is None else revenue_growth / 0.6, 12)
    put("fundamental:acceleration", None if acceleration is None else (acceleration + 0.2) / 0.4, 8)
    put("fundamental:margin_trend", None if margin_change is None else (margin_change + 0.05) / 0.1, 6)
    put("fundamental:fcf_improving", None if fcf_change_positive is None else float(fcf_change_positive), 4)
    put("catalyst:dated_3_12m", None if dated_catalysts_3_12m is None else dated_catalysts_3_12m / 3, 8)
    put("catalyst:gov_awards", None if gov_award_value_to_revenue is None else gov_award_value_to_revenue / 0.2, 6)
    put("catalyst:policy_links", None if verified_policy_links is None else verified_policy_links / 3, 6)
    put("valuation:not_already_moved", None if return_12m is None else 1 - (return_12m + 0.2) / 1.5, 10)
    put("valuation:below_52w_high", None if pct_below_52w_high is None else pct_below_52w_high / 0.6, 4)
    put("valuation:ev_revenue_vs_growth", None if ev_revenue is None or revenue_growth is None or ev_revenue <= 0
        else 1 - min((ev_revenue / max(revenue_growth * 100, 1)) / 0.3, 1), 8)
    total_w = sum(w for _, w in comps.values())
    score = round(sum(v * w for v, w in comps.values()) / total_w * 100, 1) if total_w else None
    return DiscoveryScore(score=score, components={k: round(v, 3) for k, (v, _) in comps.items()}, missing=missing)
