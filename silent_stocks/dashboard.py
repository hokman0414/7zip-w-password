"""Streamlit dashboard over the latest persisted run (streamlit run silent_stocks/dashboard.py)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from silent_stocks.config import DEFAULT_WATCHLIST, get_settings
from silent_stocks.db import Store
from silent_stocks.policy_graph import graph

st.set_page_config(page_title="Silent Stocks", layout="wide")
settings = get_settings()
store = Store(settings.db_path)
reports = store.latest_reports()

st.title("Silent Stocks — STEMPLE research dashboard")
st.caption("Research output only. No orders are placed. The 80/100 vote gate is an evidence threshold, "
           "not an 80% probability of doubling. UNKNOWN votes never count as YES.")
if not reports:
    st.warning("No completed run in the database. Run `silent-stocks daily` (or `silent-stocks demo`).")
    st.stop()

run = reports[0].run_id
st.write(f"Run `{run}` as of {reports[0].as_of:%Y-%m-%d %H:%M} UTC")
if any("demo" in (r.price_source or "") for r in reports):
    st.error("DEMO run: synthetic fixture data.")

rows = []
for r in reports:
    bull = next((s for s in r.valuation.scenarios if s.name == "bull"), None)
    rows.append({"ticker": r.ticker, "group": "watchlist" if r.ticker in DEFAULT_WATCHLIST else "discovery",
                 "status": r.status.value, "price": r.price, "indep_yes": r.tally.independent_yes, "yes": r.tally.yes,
                 "no": r.tally.no, "unknown": r.tally.unknown, "discovery": r.discovery_score,
                 "ev_rev": r.valuation.ev_revenue, "bull_upside": bull.upside_pct if bull else None,
                 "mc_p_double": r.valuation.monte_carlo.p_double if r.valuation.monte_carlo else None,
                 "critical_vetoes": ", ".join(v.code for v in r.vetoes if v.severity == "critical")})
df = pd.DataFrame(rows)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Analyzed", len(df))
c2.metric("Qualified", int((df.status == "QUALIFIED").sum()))
c3.metric("Under review", int((df.status == "UNDER REVIEW").sum()))
c4.metric("Disqualified / stale", int(df.status.isin(["DISQUALIFIED", "STALE DATA"]).sum()))

tab_over, tab_co, tab_policy, tab_port, tab_alerts = st.tabs(["Overview", "Company", "Policy graph", "Portfolio & proposals", "Alerts"])
with tab_over:
    st.subheader("Watchlist")
    st.dataframe(df[df.group == "watchlist"].drop(columns="group"), width="stretch", hide_index=True)
    st.subheader("Top discoveries (by Silent Stock Discovery Score)")
    st.caption("Low attention is not evidence of undervaluation. Analyst coverage and 13F ownership are not configured and are excluded from the score.")
    st.dataframe(df[df.group == "discovery"].sort_values("discovery", ascending=False).head(20).drop(columns="group"),
                 width="stretch", hide_index=True)

with tab_co:
    t = st.selectbox("Ticker", df.ticker.tolist())
    r = next(x for x in reports if x.ticker == t)
    st.header(f"{r.ticker} — {r.company}: {r.status.value}")
    st.write(r.discovery_components.get("_status_reason"))
    st.write(f"Price {r.price} from {r.price_source} at {r.price_time}")
    a, b, c = st.columns(3)
    a.metric("Independent YES", f"{r.tally.independent_yes}/100", f"{r.tally.dependent_yes} collapsed duplicates")
    b.metric("NO", r.tally.no)
    c.metric("UNKNOWN (abstain)", r.tally.unknown)
    st.caption(r.tally.disclaimer)
    for v in r.vetoes:
        (st.error if v.severity == "critical" else st.warning)(f"{v.code}: {v.description}")
    st.subheader("STEMPLE")
    st.dataframe(pd.DataFrame([d.model_dump(exclude={"evidence_ids"}) for d in r.stemple]), hide_index=True, width="stretch")
    st.subheader("Valuation")
    v = r.valuation
    st.json({k: getattr(v, k) for k in ("enterprise_value", "revenue_ttm", "revenue_growth_yoy", "gross_margin", "ev_revenue",
                                         "peer_ev_revenue_median", "price_to_double", "revenue_required_to_double_at_current_multiple",
                                         "growth_required_to_double_at_current_multiple", "bull_meets_double", "notes")})
    if v.scenarios:
        st.dataframe(pd.DataFrame([{"scenario": s.name, "price": s.implied_price, "upside": s.upside_pct, **{k: s.assumptions[k] for k in ("revenue_growth", "ev_revenue", "dilution")}} for s in v.scenarios]), hide_index=True)
    if v.monte_carlo:
        st.write(f"Monte Carlo ({v.monte_carlo.simulations} sims, seed {v.monte_carlo.seed}): P(>=2x) {v.monte_carlo.p_double:.1%}, P(<=0.5x) {v.monte_carlo.p_loss_50:.1%}")
        st.caption(v.monte_carlo.label)
    st.subheader("Structured analytic techniques")
    for tq in r.techniques:
        with st.expander(f"{tq.technique}{'' if tq.applied else ' (not applied)'}: {tq.summary[:140]}"):
            st.json(tq.details)
    st.subheader("Catalysts")
    st.dataframe(pd.DataFrame([c.model_dump() for c in r.catalysts]) if r.catalysts else pd.DataFrame(), hide_index=True)
    st.subheader("Could double / could fail")
    l, rr = st.columns(2)
    l.write("\n".join(f"- {x}" for x in r.reasons_could_double) or "-")
    rr.write("\n".join(f"- {x}" for x in r.reasons_could_fail) or "-")
    st.subheader("100 assignments")
    st.dataframe(pd.DataFrame([{"id": x.assignment_id, "group": x.group, "dimension": x.dimension, "vote": x.vote.value,
                                "conf": x.confidence, "question": x.question, "finding": x.finding, "dup_of": x.dependent_on,
                                "executor": x.executor, "sources": len(x.source_urls)} for x in r.assignments]),
                 hide_index=True, width="stretch", height=400)
    st.subheader("Evidence")
    st.dataframe(pd.DataFrame([{"type": e.evidence_type.value, "sentiment": e.sentiment.value, "claim": e.claim,
                                "source": e.source_url, "date": e.published_date, "provider": e.provider} for e in r.evidence]),
                 hide_index=True, width="stretch", height=300)
    st.subheader("Data gaps")
    st.write("\n".join(f"- {g}" for g in r.data_gaps))
    hist = store.history(r.ticker)
    if len(hist) > 1:
        st.line_chart(pd.DataFrame(hist).set_index("as_of")[["independent_yes"]])

with tab_policy:
    chains = [c for r in reports for c in r.policy_chains]
    g = graph(chains, [])
    st.write(f"{len(g['nodes'])} nodes, {len(g['edges'])} edges. Company edges exist only for sourced company-specific links.")
    st.dataframe(pd.DataFrame([c.model_dump(exclude={"evidence_ids"}) for c in chains]), hide_index=True, width="stretch")

with tab_port:
    props = store.proposals()
    st.warning("Every proposal requires your approval. Nothing here is submitted. To act, review each with Robinhood "
               "`review_equity_order` and approve manually.")
    st.dataframe(pd.DataFrame([{k: v for k, v in p.items() if k != "review_equity_order"} for p in props]), hide_index=True, width="stretch")
    for p in props:
        if "review_equity_order" in p:
            with st.expander(f"{p['side'].upper()} {p['symbol']} — review_equity_order parameters"):
                st.json(p["review_equity_order"])

with tab_alerts:
    st.dataframe(pd.DataFrame(store.alerts()), hide_index=True, width="stretch")
