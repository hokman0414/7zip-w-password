"""Comparable pricing model for lab-grown marquise diamonds."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pandas as pd

from src.models import utc_now

# Asking prices observed/collected during this investigation. Not transaction prices.
COMPARABLES = [
    {"source": "Jewelry by Cleo", "url": "https://jewelrybycleo.com/products/3-03ct-marquise-lab-grown-diamond-colour-f-clarity-vs1-igi-certified", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "LG726561176", "price_usd": 624, "price_type": "retail_ask", "dims": "14.76x7.67x4.68"},
    {"source": "Laura Milman", "url": "https://www.lauramilman.com/products/lg-100759907944", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "unknown", "price_usd": 675, "price_type": "retail_ask", "dims": "15.75x7.55x4.52"},
    {"source": "Aurélinne", "url": "https://aurelinne.com/products/3-03ct-marquise-lab-grown-diamond-colour-f-clarity-vs1-igi-certified-2", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "LG747592527", "price_usd": 736, "price_type": "retail_ask_sold_out", "dims": "15.11x7.57x4.68"},
    {"source": "B2C Jewels", "url": "https://www.b2cjewels.com/dd/31446716/marquise-diamond-F-color-VS1-Clarity", "carat": 2.85, "color": "F", "clarity": "VS1", "cert": "LG747565892", "price_usd": 947, "price_type": "retail_ask_oos", "dims": "14.61x7.42x4.61"},
    {"source": "Hadar Diamonds", "url": "https://hadardiamonds.com/products/3-03-ct-marquise-lab-grown-diamond-757bd528lg048", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "unknown", "price_usd": 1267.15, "price_type": "retail_ask", "dims": "unknown"},
    {"source": "Von Diamonds", "url": "https://vondiamonds.com/products/kd-100742809318", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "unknown", "price_usd": 1725, "price_type": "retail_ask", "dims": "unknown"},
    {"source": "Laura Milman 2.8", "url": "https://www.lauramilman.com/products/lg-100756993369", "carat": 2.8, "color": "F", "clarity": "VS1", "cert": "unknown", "price_usd": 1285, "price_type": "retail_ask", "dims": "15.49x7.38x4.46"},
    {"source": "Friendly Diamonds 2.90", "url": "https://friendlydiamonds.com/loose-diamonds/marquise-2.9-f-vs1-excellent-5439279", "carat": 2.90, "color": "F", "clarity": "VS1", "cert": "unknown", "price_usd": 1206, "price_type": "retail_ask_oos", "dims": "14.71x7.33x4.71"},
    {"source": "The Diamond Lab 2.96", "url": "https://www.thediamondlab.net/products/los-00388", "carat": 2.96, "color": "F", "clarity": "VS1", "cert": "677502632", "price_usd": 1420.8, "price_type": "retail_ask", "dims": "unknown"},
    {"source": "Jewelry Exchange 3.1", "url": "https://jewelryexchange.com/product/lab-grown-3-1-carat-f-vs1-marquise-igi-diamond/", "carat": 3.1, "color": "F", "clarity": "VS1", "cert": "LG607300761", "price_usd": 1856.9, "price_type": "retail_ask", "dims": "15.52x7.47x4.60"},
    {"source": "Ritani nearby 2.90 G/VS1", "url": "https://www.ritani.com/products/2-90-carat-marquise-lab-diamond-very-good-cut-g-color-vs1-clarity-igi-lg841603382-sku-d-3s59oijfhy", "carat": 2.90, "color": "G", "clarity": "VS1", "cert": "LG841603382", "price_usd": 680, "price_type": "retail_ask_near_comp", "dims": "14.39x7.63x4.66"},
    {"source": "Ritani nearby 2.90 H/VS1", "url": "https://www.ritani.com/products/2-90-carat-marquise-lab-diamond-very-good-cut-h-color-vs1-clarity-igi-lg841660876-sku-d-3s59oiknv0", "carat": 2.90, "color": "H", "clarity": "VS1", "cert": "LG841660876", "price_usd": 616, "price_type": "retail_ask_near_comp", "dims": "14.39x7.66x4.7"},
    {"source": "Shopify storefront F/VVS2 3.03", "url": "https://azt0aw-u9.myshopify.com/products/3-03ct-marquise-f-vvs2-diamond-l7n8", "carat": 3.03, "color": "F", "clarity": "VVS2", "cert": "LG739542088", "price_usd": 1119.72, "price_type": "retail_ask_near_comp", "dims": "14.39x7.67x4.82"},
    {"source": "Reddit community heuristic", "url": "https://www.reddit.com/r/labdiamond/comments/1vwjjf6/7ct_emerald_cut_f_vvs2/", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "n/a", "price_usd": 303, "price_type": "community_rule_of_thumb_100_per_ct", "dims": "n/a"},
    {"source": "Mashable market commentary band mid", "url": "https://mashable.com/life/tiktok-shop-lab-grown-diamond-live-auctions", "carat": 3.03, "color": "F", "clarity": "VS1", "cert": "n/a", "price_usd": 454.5, "price_type": "media_stated_band_150_per_ct", "dims": "n/a"},
]


def analyze_pricing(purchase_price: float = 350.0) -> dict:
    df = pd.DataFrame(COMPARABLES)
    df["ppc"] = df["price_usd"] / df["carat"]

    retail = df[df["price_type"].str.startswith("retail_ask")].copy()
    tight = retail[(retail["color"] == "F") & (retail["clarity"] == "VS1") & (retail["carat"].between(2.8, 3.2))]
    prices = tight["price_usd"].tolist()
    ppcs = tight["ppc"].tolist()

    def iqr(vals: list[float]) -> tuple[float, float]:
        if len(vals) < 4:
            return (min(vals), max(vals)) if vals else (float("nan"), float("nan"))
        q1 = statistics.quantiles(vals, n=4)[0]
        q3 = statistics.quantiles(vals, n=4)[2]
        return q1, q3

    q1, q3 = iqr(prices)
    # outlier-adjusted: exclude outside 1.5*IQR when enough points
    if len(prices) >= 4 and q3 > q1:
        fence_low, fence_high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        adj = [p for p in prices if fence_low <= p <= fence_high]
    else:
        adj = prices

    median_ask = statistics.median(prices) if prices else None
    median_ppc = statistics.median(ppcs) if ppcs else None
    purchase_ppc = purchase_price / 3.03

    assessment = {
        "economically_plausible": True,
        "unusually_favorable_vs_retail_asks": bool(median_ask and purchase_price < 0.7 * median_ask),
        "consistent_with_auction_liquidation": True,
        "below_credible_acquisition_cost": "UNKNOWN",
        "suspicious_vs_verified_wholesale": "UNKNOWN",
        "rationale": (
            f"${purchase_price} (~${purchase_ppc:.0f}/ct) sits below the observed retail-ask cluster "
            f"for similar F/VS1 marquises, but community heuristics (~$100/ct) and media bands "
            f"(~$100–200/ct) make auction pricing plausible. Without a verified wholesale feed for "
            f"LG839637366, 'below cost' cannot be confirmed."
        ),
    }

    result = {
        "target": {
            "shape": "marquise",
            "carat_range": [2.8, 3.2],
            "color": "F",
            "clarity": "VS1",
            "lab": "IGI",
            "purchase_price_usd": purchase_price,
            "purchase_ppc": round(purchase_ppc, 2),
        },
        "comparables_count": int(len(tight)),
        "comparables": tight.to_dict(orient="records"),
        "all_rows_including_near_comps": df.to_dict(orient="records"),
        "stats_retail_asks_F_VS1": {
            "n": len(prices),
            "min": round(min(prices), 2) if prices else None,
            "max": round(max(prices), 2) if prices else None,
            "median": round(median_ask, 2) if median_ask is not None else None,
            "iqr": [round(q1, 2), round(q3, 2)] if prices else None,
            "outlier_adjusted_median": round(statistics.median(adj), 2) if adj else None,
            "median_price_per_carat": round(median_ppc, 2) if median_ppc is not None else None,
            "price_type_caveat": "These are asking prices, not verified transaction prices.",
        },
        "auction_discount_vs_median_ask": (
            round(1 - (purchase_price / median_ask), 3) if median_ask else None
        ),
        "unverified_leads": {
            "ritani_ask_usd": 945,
            "ritani_wholesale_estimate_usd": 325.97,
            "brilliance_ask_usd": 2020,
            "status": "UNVERIFIED",
        },
        "assessment": assessment,
        "limitations": [
            "Retail asks ≠ clearing prices",
            "Cut quality / light performance not priced here",
            "Some listings OOS or near-comps (G/H color, VVS2)",
            "No verified wholesale invoice for this certificate",
        ],
        "collected_at_utc": utc_now().isoformat(),
    }
    out = Path(__file__).resolve().parents[1] / "research" / "market" / "pricing_analysis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    return result