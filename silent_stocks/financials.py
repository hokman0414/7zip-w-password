"""Point-in-time fundamentals derived from SEC XBRL company facts.

Every fact is filtered by its `filed` date <= as_of, so analysis at a historical date only sees what was public
then (no look-ahead). Quarterly values are reconstructed from 3-month facts and from year-to-date differences
(cash-flow statements are usually reported YTD only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .connectors.sec_edgar import facts_for, filing_index_url
from .models import Evidence, EvidenceType, Sentiment

REVENUE = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet",
           "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST_OF_REVENUE = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"]
GROSS_PROFIT = ["GrossProfit"]
OPERATING_INCOME = ["OperatingIncomeLoss"]
NET_INCOME = ["NetIncomeLoss", "ProfitLoss"]
DA = ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"]
CFO = ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]
CAPEX = ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]
CASH = ["CashAndCashEquivalentsAtCarryingValue", "Cash", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]
SHORT_INV = ["ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"]
DEBT_PARTS = [["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "ConvertibleNotesPayableNoncurrent",
               "LongTermNotesPayable", "SeniorNotes"],
              ["LongTermDebtCurrent", "DebtCurrent", "ConvertibleNotesPayableCurrent", "ShortTermBorrowings"]]
DEBT_TOTAL = ["LongTermDebt", "DebtInstrumentCarryingAmount"]
BACKLOG = ["RevenueRemainingPerformanceObligation"]
EQUITY = ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
SBC = ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]


@dataclass
class Point:
    start: date | None
    end: date
    value: float
    filed: date
    accession: str
    form: str


@dataclass
class Fundamentals:
    cik: int
    name: str
    as_of: date
    revenue_q: list[Point] = field(default_factory=list)
    metrics: dict[str, float | None] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    last_filed: date | None = None
    gaps: list[str] = field(default_factory=list)

    def m(self, key: str) -> float | None:
        return self.metrics.get(key)


def _d(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def _points(facts: dict, concepts: list[str], as_of: date, taxonomy: str = "us-gaap", unit: str | None = None) -> tuple[list[Point], str | None]:
    """Concepts are merged per period in priority order (filers switch tags over time). Within a concept, the
    latest filing <= as_of wins, which applies restatements without look-ahead."""
    merged: dict[tuple, Point] = {}
    used: str | None = None
    for concept in concepts:
        raw = facts_for(facts, concept, taxonomy=taxonomy, unit=unit)
        best: dict[tuple, Point] = {}
        for f in raw:
            filed = _d(f.get("filed"))
            if filed is None or filed > as_of or f.get("val") is None:
                continue
            p = Point(_d(f.get("start")), _d(f["end"]), float(f["val"]), filed, f.get("accn", ""), f.get("form", ""))
            key = (p.start, p.end)
            if key not in best or p.filed >= best[key].filed:
                best[key] = p
        for key, p in best.items():
            if key not in merged:
                merged[key] = p
                used = used or concept
    return sorted(merged.values(), key=lambda p: (p.end, p.start or p.end)), used


def quarterize(points: list[Point]) -> list[Point]:
    """3-month values from direct quarterly facts, YTD differences, and FY minus three quarters."""
    quarters: dict[date, Point] = {}
    by_start: dict[date, list[Point]] = {}
    for p in points:
        if p.start is None:
            continue
        days = (p.end - p.start).days
        if 80 <= days <= 100:
            quarters[p.end] = p
        by_start.setdefault(p.start, []).append(p)
    for start, group in by_start.items():
        group = sorted(group, key=lambda p: p.end)
        for prev, cur in zip(group, group[1:]):
            gap = (cur.end - prev.end).days
            if 80 <= gap <= 100 and cur.end not in quarters:
                quarters[cur.end] = Point(prev.end + timedelta(days=1), cur.end, cur.value - prev.value,
                                          cur.filed, cur.accession, cur.form)
    for p in points:
        if p.start is None or not (350 <= (p.end - p.start).days <= 380) or p.end in quarters:
            continue
        inside = [q for q in quarters.values() if q.start and q.start >= p.start - timedelta(days=5) and q.end < p.end]
        if len(inside) == 3:
            quarters[p.end] = Point(max(q.end for q in inside) + timedelta(days=1), p.end,
                                    p.value - sum(q.value for q in inside), p.filed, p.accession, p.form)
    return sorted(quarters.values(), key=lambda p: p.end)


def _ttm(quarters: list[Point], offset: int = 0) -> tuple[float | None, list[Point]]:
    if len(quarters) < 4 + offset:
        return None, []
    window = quarters[len(quarters) - 4 - offset: len(quarters) - offset]
    span = (window[-1].end - window[0].end).days
    if not 250 <= span <= 300:
        return None, []
    return sum(q.value for q in window), window


def _latest_instant(points: list[Point]) -> Point | None:
    inst = [p for p in points if p.start is None]
    return inst[-1] if inst else None


def _instant_near(points: list[Point], target: date, tol_days: int = 45) -> Point | None:
    inst = [p for p in points if p.start is None and abs((p.end - target).days) <= tol_days]
    return min(inst, key=lambda p: abs((p.end - target).days)) if inst else None


def compute_fundamentals(cik: int, facts: dict, as_of: date) -> Fundamentals:
    name = facts.get("entityName", "")
    fx = Fundamentals(cik=cik, name=name, as_of=as_of)
    base_title = f"SEC XBRL company facts: {name}"

    def ev(metric: str, value: float | None, point: Point | None, claim: str, sentiment: Sentiment = Sentiment.NEUTRAL):
        fx.metrics[metric] = value
        if value is None or point is None:
            return
        fx.evidence[metric] = Evidence(
            claim=claim, source_url=filing_index_url(cik, point.accession) if point.accession else
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
            source_title=f"{base_title} ({point.form} filed {point.filed})", published_date=point.filed,
            evidence_type=EvidenceType.VERIFIED, provider="sec-xbrl", metric=metric, value=value, sentiment=sentiment,
        )

    rev_pts, _ = _points(facts, REVENUE, as_of)
    rev_q = quarterize(rev_pts)
    fx.revenue_q = rev_q
    filed_dates = [p.filed for p in rev_pts]
    fx.last_filed = max(filed_dates) if filed_dates else None

    rev_ttm, win = _ttm(rev_q)
    rev_prior, _ = _ttm(rev_q, offset=4)
    last = win[-1] if win else None
    ev("revenue_ttm", rev_ttm, last, f"Trailing-12-month revenue ${rev_ttm or 0:,.0f} (quarters ending {last.end if last else '?'})")
    growth = (rev_ttm / rev_prior - 1) if rev_ttm and rev_prior and rev_prior > 0 else None
    ev("revenue_growth_yoy", growth, last, f"TTM revenue growth {growth:.1%} year over year" if growth is not None else "",
       Sentiment.POSITIVE if (growth or 0) > 0.15 else Sentiment.NEGATIVE if (growth or 0) < 0 else Sentiment.NEUTRAL)

    if len(rev_q) >= 6:
        def q_yoy(i: int) -> float | None:
            cur, prior = rev_q[i], next((q for q in rev_q if 350 <= (rev_q[i].end - q.end).days <= 380), None)
            return cur.value / prior.value - 1 if prior and prior.value > 0 else None
        g_last, g_prev = q_yoy(len(rev_q) - 1), q_yoy(len(rev_q) - 2)
        ev("revenue_q_yoy", g_last, rev_q[-1], f"Latest-quarter revenue growth {g_last:.1%} YoY" if g_last is not None else "")
        accel = (g_last - g_prev) if g_last is not None and g_prev is not None else None
        ev("revenue_acceleration", accel, rev_q[-1],
           f"Quarterly YoY growth changed by {accel:+.1%} points vs prior quarter" if accel is not None else "",
           Sentiment.POSITIVE if (accel or 0) > 0 else Sentiment.NEGATIVE)
    else:
        fx.gaps.append("fewer than 6 reconstructable revenue quarters")

    def ttm_of(concepts: list[str], offset: int = 0):
        pts, _ = _points(facts, concepts, as_of)
        q = quarterize(pts)
        val, w = _ttm(q, offset)
        return val, (w[-1] if w else None)

    gp, gp_pt = ttm_of(GROSS_PROFIT)
    if gp is None:
        cor, gp_pt = ttm_of(COST_OF_REVENUE)
        gp = rev_ttm - cor if (cor is not None and rev_ttm) else None
    gm = gp / rev_ttm if gp is not None and rev_ttm else None
    ev("gross_margin", gm, gp_pt, f"TTM gross margin {gm:.1%}" if gm is not None else "")
    gp_prior, _ = ttm_of(GROSS_PROFIT, offset=4)
    gm_prior = gp_prior / rev_prior if gp_prior is not None and rev_prior else None
    gm_delta = gm - gm_prior if gm is not None and gm_prior is not None else None
    ev("gross_margin_change", gm_delta, gp_pt, f"Gross margin changed {gm_delta:+.1%} points YoY" if gm_delta is not None else "",
       Sentiment.POSITIVE if (gm_delta or 0) > 0 else Sentiment.NEGATIVE)

    op, op_pt = ttm_of(OPERATING_INCOME)
    om = op / rev_ttm if op is not None and rev_ttm else None
    ev("operating_income_ttm", op, op_pt, f"TTM operating income ${op or 0:,.0f}")
    ev("operating_margin", om, op_pt, f"TTM operating margin {om:.1%}" if om is not None else "")
    op_prior, _ = ttm_of(OPERATING_INCOME, offset=4)
    om_prior = op_prior / rev_prior if op_prior is not None and rev_prior else None
    om_delta = om - om_prior if om is not None and om_prior is not None else None
    ev("operating_margin_change", om_delta, op_pt, f"Operating margin changed {om_delta:+.1%} points YoY" if om_delta is not None else "",
       Sentiment.POSITIVE if (om_delta or 0) > 0 else Sentiment.NEGATIVE)

    ni, ni_pt = ttm_of(NET_INCOME)
    ev("net_income_ttm", ni, ni_pt, f"TTM net income ${ni or 0:,.0f}")
    da, _ = ttm_of(DA)
    ebitda = op + da if op is not None and da is not None else None
    ev("ebitda_ttm", ebitda, op_pt, f"TTM EBITDA (operating income + D&A) ${ebitda or 0:,.0f}")
    sbc, sbc_pt = ttm_of(SBC)
    ev("sbc_ttm", sbc, sbc_pt, f"TTM stock-based compensation ${sbc or 0:,.0f}")

    rd, rd_pt = ttm_of(["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"])
    ev("rd_ttm", rd, rd_pt, f"TTM R&D expense ${rd or 0:,.0f}")
    if gp is not None and rev_ttm and gp_prior is not None and rev_prior:
        gp_growth = gp / gp_prior - 1 if gp_prior > 0 else None
        ev("gross_profit_growth", gp_growth, gp_pt, f"TTM gross profit growth {gp_growth:.1%}" if gp_growth is not None else "")

    cfo, cfo_pt = ttm_of(CFO)
    capex, capex_pt = ttm_of(CAPEX)
    capex_prior_v, _ = ttm_of(CAPEX, offset=4)
    ev("capex_ttm", capex, capex_pt, f"TTM capital expenditure ${capex or 0:,.0f}")
    capex_g = capex / capex_prior_v - 1 if capex is not None and capex_prior_v and capex_prior_v > 0 else None
    ev("capex_growth", capex_g, capex_pt, f"Capex changed {capex_g:+.1%} YoY" if capex_g is not None else "")
    inv_pts, _ = _points(facts, ["InventoryNet"], as_of)
    inv = _latest_instant(inv_pts)
    if inv:
        inv_prior = _instant_near(inv_pts, inv.end - timedelta(days=365), 60)
        inv_g = inv.value / inv_prior.value - 1 if inv_prior and inv_prior.value > 0 else None
        ev("inventory_growth", inv_g, inv, f"Inventory changed {inv_g:+.1%} YoY" if inv_g is not None else "")
    fcf = cfo - (capex or 0.0) if cfo is not None else None
    ev("cfo_ttm", cfo, cfo_pt, f"TTM operating cash flow ${cfo or 0:,.0f}")
    ev("fcf_ttm", fcf, cfo_pt, f"TTM free cash flow ${fcf or 0:,.0f}",
       Sentiment.POSITIVE if (fcf or 0) > 0 else Sentiment.NEGATIVE)
    cfo_prior, _ = ttm_of(CFO, offset=4)
    capex_prior, _ = ttm_of(CAPEX, offset=4)
    fcf_prior = cfo_prior - (capex_prior or 0.0) if cfo_prior is not None else None
    fcf_delta = fcf - fcf_prior if fcf is not None and fcf_prior is not None else None
    ev("fcf_change", fcf_delta, cfo_pt, f"TTM free cash flow changed ${fcf_delta or 0:,.0f} YoY",
       Sentiment.POSITIVE if (fcf_delta or 0) > 0 else Sentiment.NEGATIVE)

    cash_pts, _ = _points(facts, CASH, as_of)
    cash_pt = _latest_instant(cash_pts)
    sti_pts, _ = _points(facts, SHORT_INV, as_of)
    sti_pt = _instant_near(sti_pts, cash_pt.end, 5) if cash_pt else None
    cash = (cash_pt.value + (sti_pt.value if sti_pt else 0.0)) if cash_pt else None
    ev("cash", cash, cash_pt, f"Cash and short-term investments ${cash or 0:,.0f} at {cash_pt.end if cash_pt else '?'}")

    debt = None
    debt_pt = None
    total_pts, _ = _points(facts, DEBT_TOTAL, as_of)
    tp = _latest_instant(total_pts)
    if tp and cash_pt and abs((tp.end - cash_pt.end).days) <= 5:
        debt, debt_pt = tp.value, tp
    else:
        parts = []
        for group in DEBT_PARTS:
            pts, _ = _points(facts, group, as_of)
            p = _instant_near(pts, cash_pt.end, 5) if cash_pt else _latest_instant(pts)
            if p:
                parts.append(p)
        if parts:
            debt, debt_pt = sum(p.value for p in parts), parts[0]
        elif cash_pt:
            debt, debt_pt = 0.0, cash_pt
            fx.gaps.append("no tagged debt found; debt assumed 0 (verify in filing)")
    ev("debt", debt, debt_pt, f"Tagged debt ${debt or 0:,.0f} (best-effort sum of XBRL debt concepts)")

    eq_pts, _ = _points(facts, EQUITY, as_of)
    eq_pt = _latest_instant(eq_pts)
    ev("stockholders_equity", eq_pt.value if eq_pt else None, eq_pt, f"Stockholders' equity ${eq_pt.value if eq_pt else 0:,.0f}",
       Sentiment.NEGATIVE if eq_pt and eq_pt.value < 0 else Sentiment.NEUTRAL)

    sh_pts, _ = _points(facts, ["EntityCommonStockSharesOutstanding"], as_of, taxonomy="dei")
    sh_pt = _latest_instant(sh_pts)
    if sh_pt is None:
        sh_pts, _ = _points(facts, ["CommonStockSharesOutstanding"], as_of)
        sh_pt = _latest_instant(sh_pts)
    ev("shares_outstanding", sh_pt.value if sh_pt else None, sh_pt, f"Shares outstanding {sh_pt.value if sh_pt else 0:,.0f}")
    dil_pts, _ = _points(facts, ["WeightedAverageNumberOfDilutedSharesOutstanding"], as_of, unit="shares")
    # Weighted averages don't sum, so only directly reported ~quarter durations are comparable. The latest
    # filing's prior-year comparative is split-restated and wins in _points (latest filed), so the ratio
    # is split-safe; cover-page share counts are not restated and only serve as a fallback.
    wq = sorted((p for p in dil_pts if p.start and 80 <= (p.end - p.start).days <= 100 and p.value > 0), key=lambda p: p.end)
    dil, dil_pt, dil_text = None, None, ""
    if wq:
        ev("diluted_shares", wq[-1].value, wq[-1], f"Weighted diluted shares {wq[-1].value:,.0f} (latest quarter)")
        yago = [p for p in wq if abs((p.end - (wq[-1].end - timedelta(days=365))).days) <= 45]
        if yago:
            dil, dil_pt = wq[-1].value / yago[-1].value - 1, wq[-1]
            dil_text = f"Weighted diluted shares changed {dil:+.1%} vs the same quarter a year earlier (split-restated)"
    if dil is None and sh_pt:
        prior = _instant_near(sh_pts, sh_pt.end - timedelta(days=365), 60)
        if prior and prior.value > 0:
            r = sh_pt.value / prior.value
            if r >= 1.9 and abs(r - round(r)) <= 0.03 * r:
                fx.gaps.append(f"cover-page share count x{r:.2f} looks like a stock split; dilution not computed")
            else:
                dil, dil_pt = r - 1, sh_pt
                dil_text = f"Share count changed {dil:+.1%} over ~12 months (cover page, not split-restated)"
    if dil_pt is not None:
        ev("dilution_yoy", dil, dil_pt, dil_text, Sentiment.NEGATIVE if dil > 0.05 else Sentiment.NEUTRAL)

    bl_pts, _ = _points(facts, BACKLOG, as_of)
    bl = _latest_instant(bl_pts)
    if bl:
        ev("backlog", bl.value, bl, f"Remaining performance obligations (backlog proxy) ${bl.value:,.0f} at {bl.end}")
        prior = _instant_near(bl_pts, bl.end - timedelta(days=365), 60)
        g = bl.value / prior.value - 1 if prior and prior.value > 0 else None
        ev("backlog_growth_yoy", g, bl, f"Backlog (RPO) changed {g:+.1%} YoY" if g is not None else "",
           Sentiment.POSITIVE if (g or 0) > 0.1 else Sentiment.NEGATIVE if (g or 0) < 0 else Sentiment.NEUTRAL)
        if rev_ttm and rev_q:
            q_rev = rev_q[-1].value
            ev("backlog_to_quarterly_revenue", bl.value / q_rev if q_rev > 0 else None, bl,
               f"Backlog / latest-quarter revenue {bl.value / q_rev:.2f}x (book-to-bill proxy)" if q_rev > 0 else "")
    else:
        fx.gaps.append("no XBRL backlog (RemainingPerformanceObligation) tag")

    # Runway only applies when operations burn cash; capex-driven negative FCF at a cash-generative
    # business (utilities, hyperscalers) is funded from operations and capital markets, not the cash pile.
    if cash is not None and fcf is not None and fcf < 0 and cfo is not None and cfo < 0:
        runway = cash / (-fcf) * 12
        ev("cash_runway_months", runway, cash_pt, f"Cash runway ~{runway:.0f} months at TTM free-cash-flow burn (operating cash flow negative)",
           Sentiment.NEGATIVE if runway < 18 else Sentiment.NEUTRAL)
    elif fcf is not None:
        fx.metrics["cash_runway_months"] = None
    for key in ("revenue_ttm", "gross_margin", "operating_margin", "fcf_ttm", "cash", "shares_outstanding"):
        if fx.metrics.get(key) is None:
            fx.gaps.append(f"missing {key}")
    return fx
