#!/usr/bin/env python3
"""CLI for Royale Diamonds OSINT investigation pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ach_analysis import build_ach
from src.corporate_research import research_corporate
from src.diamond_inventory import search_inventory
from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.igi_verification import verify_igi_report
from src.monitoring import monitor_order
from src.pricing_analysis import analyze_pricing
from src.report_generator import generate_reports
from src.reputation_analysis import analyze_reputation
from src.source_discovery import discover_sources
from src.telegram_research import research_telegram
from src.tiktok_research import research_seller
from src.username_correlation import correlate_usernames

DEFAULT_ADVERTISED = {
    "shape": "MARQUISE BRILLIANT",
    "weight": "3.03",
    "color": "F",
    "clarity": "VS1",
    "report": "LG839637366",
    "dimensions": "14.39 x 7.67 x 4.78 mm",
    "table": "61%",
    "depth": "62.3%",
    "polish": "Excellent",
    "fluorescence": "NONE",
    "growth": "CVD",
}


def cmd_investigate(args: argparse.Namespace) -> int:
    ledger = EvidenceLedger()
    collector = HttpCollector()
    try:
        discover_sources(args.case)
        igi = verify_igi_report(
            args.igi,
            advertised=DEFAULT_ADVERTISED,
            collector=collector,
            ledger=ledger,
        )
        seller = research_seller(args.name, collector=collector, ledger=ledger)
        usernames = correlate_usernames(
            seller.get("confirmed_username") or "royalediamondslive",
            collector=collector,
            ledger=ledger,
        )
        telegram = research_telegram(
            seller.get("confirmed_username") or "royalediamondslive",
            collector=collector,
            ledger=ledger,
        )
        inventory = search_inventory(args.igi, collector=collector, ledger=ledger)
        pricing = analyze_pricing(args.bid)
        corporate = research_corporate(args.name, collector=collector, ledger=ledger)
        reputation = analyze_reputation(ledger=ledger)
        tracking = monitor_order(
            case_id=args.case,
            tracking_number=args.tracking,
            purchase_date=args.purchase_date,
            ship_by_date=args.ship_by,
            collector=collector,
            ledger=ledger,
        )
        ach = build_ach(
            {
                "igi": igi,
                "seller": seller,
                "pricing": pricing,
                "tracking": tracking,
                "inventory": inventory,
                "corporate": corporate,
                "reputation": reputation,
                "telegram": telegram,
                "usernames": usernames,
            }
        )
        reports = generate_reports(args.case)
        print(json.dumps({"ok": True, "reports": reports, "leading": ach.get("current_leading_hypotheses")}, indent=2))
        return 0
    finally:
        collector.close()


def cmd_verify_diamond(args: argparse.Namespace) -> int:
    result = verify_igi_report(args.igi, advertised=DEFAULT_ADVERTISED)
    print(json.dumps(result, indent=2))
    return 0 if result.get("verification_status") == "CONFIRMED" else 2


def cmd_research_seller(args: argparse.Namespace) -> int:
    collector = HttpCollector()
    ledger = EvidenceLedger()
    try:
        seller = research_seller(args.name, collector=collector, ledger=ledger)
        correlate_usernames(
            seller.get("confirmed_username") or "royalediamondslive",
            collector=collector,
            ledger=ledger,
        )
        research_telegram(
            seller.get("confirmed_username") or "royalediamondslive",
            collector=collector,
            ledger=ledger,
        )
        research_corporate(args.name, collector=collector, ledger=ledger)
        analyze_reputation(ledger=ledger)
        print(json.dumps(seller, indent=2))
        return 0
    finally:
        collector.close()


def cmd_monitor(args: argparse.Namespace) -> int:
    result = monitor_order(
        case_id=args.case,
        tracking_number=args.tracking,
        purchase_date=args.purchase_date,
        ship_by_date=args.ship_by,
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    result = generate_reports(args.case)
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Royale Diamonds OSINT investigation CLI")
    sub = p.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("investigate", help="Run full investigation pipeline")
    inv.add_argument("--case", default="royale_diamonds")
    inv.add_argument("--igi", default="LG839637366")
    inv.add_argument("--name", default="Royale Diamonds")
    inv.add_argument("--bid", type=float, default=350.0)
    inv.add_argument("--tracking", default="9200190390470924693050")
    inv.add_argument("--purchase-date", default="2026-10-19")
    inv.add_argument("--ship-by", default=None)
    inv.set_defaults(func=cmd_investigate)

    vd = sub.add_parser("verify-diamond", help="Verify an IGI report number")
    vd.add_argument("--igi", required=True)
    vd.set_defaults(func=cmd_verify_diamond)

    rs = sub.add_parser("research-seller", help="Research seller public identity")
    rs.add_argument("--name", required=True)
    rs.set_defaults(func=cmd_research_seller)

    mon = sub.add_parser("monitor", help="Monitor order / tracking")
    mon.add_argument("--case", default="royale_diamonds")
    mon.add_argument("--tracking", default="9200190390470924693050")
    mon.add_argument("--purchase-date", default="2026-10-19")
    mon.add_argument("--ship-by", default=None)
    mon.set_defaults(func=cmd_monitor)

    rep = sub.add_parser("report", help="Generate investigation reports")
    rep.add_argument("--case", default="royale_diamonds")
    rep.set_defaults(func=cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())