import json
from pathlib import Path

from src.igi_verification import compare_advertised, parse_igi_new_payload

SAMPLE = Path(__file__).resolve().parents[1] / "evidence" / "raw" / "igi_new_LG839637366.html"


def test_parse_confirmed_report():
    assert SAMPLE.exists(), "Run investigation first to collect IGI evidence"
    parsed = parse_igi_new_payload(SAMPLE.read_bytes())
    assert parsed["found"] is True
    assert parsed["fields"]["Report Number"] == "LG839637366"
    assert parsed["fields"]["Color Grade"] == "F"
    assert "CVD" in parsed["fields"]["Comments"]
    assert parsed["fields"]["Polish"] == "VERY GOOD"


def test_empty_report_not_found():
    parsed = parse_igi_new_payload(b"")
    assert parsed["found"] is False


def test_polish_mismatch_detected():
    fields = {"Polish": "VERY GOOD", "Report Number": "LG839637366", "Comments": "CVD growth process"}
    advertised = {
        "report": "LG839637366",
        "shape": "MARQUISE BRILLIANT",
        "weight": "3.03",
        "color": "F",
        "clarity": "VS1",
        "dimensions": "14.39 x 7.67 x 4.78 mm",
        "table": "61%",
        "depth": "62.3%",
        "polish": "Excellent",
        "fluorescence": "NONE",
        "growth": "CVD",
    }
    # fill required keys used by compare
    fields.update(
        {
            "Shape And Cut": "MARQUISE BRILLIANT",
            "Carat Weight": "3.03 Carats",
            "Color Grade": "F",
            "Clarity Grade": "VS 1",
            "Measurements": "14.39 x 7.67 x 4.78 mm",
            "Table Size": "61%",
            "Total Depth": "62.3%",
            "Fluorescence": "NONE",
        }
    )
    rows = compare_advertised(fields, advertised)
    polish = next(r for r in rows if r["field"] == "polish")
    assert polish["result"] == "MISMATCH"


def test_sample_is_valid_json_array():
    data = json.loads(SAMPLE.read_text())
    assert isinstance(data, list)
    assert "LG839637366" in data[0]