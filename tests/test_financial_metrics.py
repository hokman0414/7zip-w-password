from __future__ import annotations

from datetime import date

from silent_stocks.financials import compute_fundamentals


def _f(start, end, val, filed, form="10-Q"):
    return {"start": start, "end": end, "val": val, "filed": filed, "form": form, "accn": filed}


def _inst(end, val, filed):
    return {"end": end, "val": val, "filed": filed, "form": "10-Q", "accn": filed}


QUARTERS = [("2025-07-01", "2025-09-30", "2025-10-25"), ("2025-10-01", "2025-12-31", "2026-01-25"),
            ("2026-01-01", "2026-03-31", "2026-04-25"), ("2026-04-01", "2026-06-30", "2026-07-25"),
            ("2026-07-01", "2026-09-30", "2026-10-25")]


def _facts(gaap: dict, dei: dict | None = None) -> dict:
    return {"entityName": "X", "facts": {"us-gaap": gaap, "dei": dei or {}}}


def test_stock_split_is_not_dilution():
    # 10-for-1 split in 2026: the latest 10-Q restates the year-ago quarter to 4.3B; cover page jumps 10x.
    diluted = [_f("2025-07-01", "2025-09-30", 430e6, "2025-10-25"),
               _f("2025-07-01", "2025-09-30", 4300e6, "2026-10-25"),
               _f("2026-07-01", "2026-09-30", 4330e6, "2026-10-25")]
    cover = [_inst("2025-10-15", 428e6, "2025-10-25"), _inst("2026-10-15", 4280e6, "2026-10-25")]
    fx = compute_fundamentals(1, _facts({"WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": diluted}}},
                                        {"EntityCommonStockSharesOutstanding": {"units": {"shares": cover}}}), date(2026, 11, 6))
    assert abs(fx.metrics["dilution_yoy"] - (4330 / 4300 - 1)) < 1e-9


def test_cover_page_split_ratio_without_restated_weighted_shares_is_skipped():
    cover = [_inst("2025-10-15", 428e6, "2025-10-25"), _inst("2026-10-15", 4280e6, "2026-10-25")]
    fx = compute_fundamentals(1, _facts({}, {"EntityCommonStockSharesOutstanding": {"units": {"shares": cover}}}), date(2026, 11, 6))
    assert fx.metrics.get("dilution_yoy") is None
    assert any("stock split" in g for g in fx.gaps)


def test_real_dilution_still_detected():
    diluted = [_f("2025-07-01", "2025-09-30", 100e6, "2025-10-25"), _f("2026-07-01", "2026-09-30", 145e6, "2026-10-25")]
    fx = compute_fundamentals(1, _facts({"WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": diluted}}}), date(2026, 11, 6))
    assert abs(fx.metrics["dilution_yoy"] - 0.45) < 1e-9


def _cash_flow_facts(cfo_q: float, capex_q: float) -> dict:
    return _facts({
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [_f(s, e, cfo_q, fl) for s, e, fl in QUARTERS]}},
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [_f(s, e, capex_q, fl) for s, e, fl in QUARTERS]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [_inst("2026-09-30", 300e6, "2026-10-25")]}},
    })


def test_capex_funded_negative_fcf_has_no_runway():
    fx = compute_fundamentals(1, _cash_flow_facts(cfo_q=3e9, capex_q=3.3e9), date(2026, 11, 6))
    assert fx.metrics["fcf_ttm"] < 0
    assert fx.metrics.get("cash_runway_months") is None


def test_operating_burn_has_runway():
    fx = compute_fundamentals(1, _cash_flow_facts(cfo_q=-40e6, capex_q=10e6), date(2026, 11, 6))
    assert abs(fx.metrics["cash_runway_months"] - 300e6 / 200e6 * 12) < 1e-6
