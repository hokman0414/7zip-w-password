"""Official IGI report verification via public lookup endpoint."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.evidence_ledger import EvidenceLedger
from src.http_util import HttpCollector
from src.models import ClaimStatus, EvidenceRecord, EvidenceTier, Reliability, utc_now

IGI_NEW = "https://lookup.igi.org/igi_new.php?r={report}"
IGI_PAGE = "https://lookup.igi.org/index.php/reports/verify_your_report?r={report}"


def parse_igi_new_payload(raw: bytes | str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else raw
    text = text.strip()
    if not text:
        return {"found": False, "fields": {}, "raw_empty": True}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"found": False, "fields": {}, "parse_error": "not_json", "raw_excerpt": text[:500]}
    if not payload or not payload[0]:
        return {"found": False, "fields": {}}
    html = payload[0]
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}
    for tr in soup.select("tr"):
        tds = tr.find_all("td")
        if len(tds) == 2:
            k = tds[0].get_text(" ", strip=True)
            v = tds[1].get_text(" ", strip=True)
            if k:
                fields[k] = re.sub(r"\s+", " ", v).strip()
    plot = None
    if len(payload) > 3 and isinstance(payload[3], str) and "http" in payload[3]:
        m = re.search(r'src=\\"([^\\]+)\\"', payload[3]) or re.search(r'src="([^"]+)"', payload[3])
        if m:
            plot = m.group(1)
        else:
            m2 = re.search(r"https://[^\"'\\]+", payload[3])
            if m2:
                plot = m2.group(0)
    return {
        "found": bool(fields.get("Report Number")),
        "fields": fields,
        "plot_image_url": plot,
        "payload_meta": {
            "type_flag": payload[4] if len(payload) > 4 else None,
            "origin_flag": payload[5] if len(payload) > 5 else None,
        },
    }


def compare_advertised(fields: dict[str, str], advertised: dict[str, Any]) -> list[dict[str, str]]:
    rows = []

    def add(field: str, igi_key: str, advertised_value: str, normalize=True):
        igi = fields.get(igi_key, "")
        adv = advertised_value or ""
        if normalize:
            a = re.sub(r"\s+", "", igi.upper())
            b = re.sub(r"\s+", "", adv.upper().replace("×", "X").replace("×", "X"))
            b = b.replace("VS1", "VS1").replace("VS 1", "VS1")
            a2 = a.replace("VS1", "VS1")
            # special polish mismatch handling done by caller expectations
            match = b in a2 or a2 in b or a2 == b
        else:
            match = igi == adv
        rows.append(
            {
                "field": field,
                "igi": igi,
                "advertised": adv,
                "result": "MATCH" if match else "MISMATCH",
            }
        )

    add("report_number", "Report Number", advertised.get("report", ""))
    add("shape", "Shape And Cut", advertised.get("shape", "MARQUISE BRILLIANT"))
    add("carat", "Carat Weight", f"{advertised.get('weight', '')} Carats")
    add("color", "Color Grade", advertised.get("color", ""))
    add("clarity", "Clarity Grade", advertised.get("clarity", "").replace("VS1", "VS 1"))
    add("measurements", "Measurements", advertised.get("dimensions", "").replace("×", "x"))
    add("table", "Table Size", advertised.get("table", ""))
    add("depth", "Total Depth", advertised.get("depth", ""))
    add("fluorescence", "Fluorescence", advertised.get("fluorescence", "NONE"))
    add("polish", "Polish", advertised.get("polish", ""))
    # growth
    comments = fields.get("Comments", "")
    growth_adv = advertised.get("growth", "CVD")
    growth_ok = growth_adv.upper() in comments.upper()
    rows.append(
        {
            "field": "growth_method",
            "igi": comments,
            "advertised": growth_adv,
            "result": "MATCH" if growth_ok else "MISMATCH",
        }
    )
    return rows


def verify_igi_report(
    report_number: str,
    advertised: dict[str, Any] | None = None,
    collector: HttpCollector | None = None,
    ledger: EvidenceLedger | None = None,
) -> dict[str, Any]:
    owns = collector is None
    collector = collector or HttpCollector()
    ledger = ledger or EvidenceLedger()
    advertised = advertised or {}
    url = IGI_NEW.format(report=report_number)
    meta = collector.get(url, cache_key=f"igi_new_{report_number}", respect_robots=True)
    local_path = None
    sha = meta.get("sha256")
    if meta.get("content"):
        local_path, sha = collector.preserve(f"igi_new_{report_number}.html", meta["content"])
        local_path = str(local_path)

    parsed = parse_igi_new_payload(meta.get("content") or b"")
    status = ClaimStatus.CONFIRMED if parsed.get("found") else ClaimStatus.MISSING
    if meta.get("status") in {"error", "robots_disallowed", "http_error"} and not parsed.get("found"):
        status = ClaimStatus.BLOCKED

    comparisons = compare_advertised(parsed.get("fields", {}), advertised) if advertised else []
    polish_mismatch = any(
        r["field"] == "polish" and r["result"] == "MISMATCH" for r in comparisons
    )

    result = {
        "report_number": report_number,
        "verification_status": status.value,
        "source_url": url,
        "verify_page": IGI_PAGE.format(report=report_number),
        "http_status": meta.get("http_status"),
        "fields": parsed.get("fields", {}),
        "plot_image_url": parsed.get("plot_image_url"),
        "comparisons": comparisons,
        "manual_checkpoint": None,
        "collected_at_utc": utc_now().isoformat(),
        "local_path": local_path,
        "sha256": sha,
    }
    if status != ClaimStatus.CONFIRMED:
        result["manual_checkpoint"] = {
            "task": "Manually verify IGI report in a normal browser",
            "steps": [
                f"Open {IGI_PAGE.format(report=report_number)}",
                "Confirm report number, shape, and carat weight",
                "Screenshot the REPORT RESULT panel and Download PDF if available",
                "Provide the screenshot/PDF path to re-ingest into evidence/raw",
            ],
        }

    ledger.append(
        EvidenceRecord(
            evidence_id=f"igi_{report_number}",
            source_url=url,
            source_title=f"IGI report {report_number}",
            local_path=local_path,
            sha256=sha,
            source_category="diamond_cert",
            reliability=Reliability.A,
            evidence_tier=EvidenceTier.PRIMARY,
            status=status,
            extracted_facts={
                "fields": parsed.get("fields", {}),
                "polish_mismatch_vs_advertised": polish_mismatch,
            },
            notes="Official IGI igi_new.php lookup; empty body indicates missing report.",
        )
    )

    out = Path(__file__).resolve().parents[1] / "research" / "diamonds" / f"igi_{report_number}_verified.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    if owns:
        collector.close()
    return result