"""Optional Streamlit monitoring dashboard.

Run: streamlit run src/dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    path = ROOT / name
    if path.exists():
        return json.loads(path.read_text())
    return {}


def main() -> None:
    try:
        import streamlit as st
    except ImportError:
        print("Install streamlit to use the dashboard: pip install streamlit")
        return

    st.set_page_config(page_title="Royale Diamonds OSINT", layout="wide")
    st.title("Royale Diamonds — Investigation Dashboard")

    exec_ = load("reports/executive_assessment.json")
    mon = load("analysis/monitoring_royale_diamonds.json")
    ach = load("analysis/ach_matrix.json")
    igi = load("research/diamonds/igi_LG839637366_verified.json")

    c1, c2, c3 = st.columns(3)
    c1.metric("IGI status", igi.get("verification_status", "UNKNOWN"))
    c2.metric("Tracking", mon.get("tracking_number") or "none")
    c3.metric("Leading H", ", ".join(ach.get("current_leading_hypotheses") or []))

    st.subheader("Shipment")
    st.write(mon.get("shipment_status"))
    st.subheader("Executive")
    st.json(exec_)
    st.subheader("ACH posteriors (subjective)")
    st.json((ach.get("subjective_bayes") or {}).get("posteriors", {}))


if __name__ == "__main__":
    main()