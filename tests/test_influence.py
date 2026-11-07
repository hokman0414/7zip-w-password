from __future__ import annotations

import json
from datetime import date, datetime, timezone

from influence_intel import analysis, demo, pathways, report, sponsorship
from influence_intel.collect import Sources, collect
from influence_intel.connectors import Fec, Lda, ProPublica, _bills, load_research
from influence_intel.models import Affiliate, Direction, EntityProfile, Evidence

AS_OF = date(2026, 11, 6)


class FakeHttp:
    def __init__(self, routes):
        self.routes = routes

    def get_json(self, url, ttl_hours=24, params=None):
        for prefix, data in self.routes.items():
            if url.startswith(prefix):
                return (data(params) if callable(data) else data), {}
        raise FileNotFoundError(url)


def _profile(**kw):
    return EntityProfile(slug="t", name="T", affiliates=[Affiliate(name="T", **kw)])


def test_demo_end_to_end_is_labelled_and_cited():
    r = report.build(demo.dataset(AS_OF), demo=True)
    assert r["demo"] and len(r["pathways"]) == len(pathways.PATHWAYS)
    assert r["sponsorship_outlook"][0]["label"] == "Education advocacy"
    for c in r["sponsorship_outlook"]:
        assert c["evidence_ids"] and all(e in r["evidence"] for e in c["evidence_ids"])
        assert 0 <= c["score"] <= 100
    assert "DEMO" in report.markdown(r)


def test_no_data_means_unknown_not_pass():
    ds = collect(_profile(), AS_OF, Sources())
    pw = pathways.assess(ds)
    assert all(p.strength is None for p in pw)
    assert sponsorship.candidates(ds) == []
    a = analysis.ach(ds, pw)
    assert a["leading"] is None and all(v is None for v in a["indicators"].values())


def test_fec_drops_individuals():
    rows = [{"entity_type": "IND", "recipient_name": "JANE DOE", "disbursement_amount": 50, "disbursement_date": "2026-03-01"},
            {"entity_type": "CCM", "recipient_name": "SMITH FOR CONGRESS", "recipient_committee_id": "C1",
             "disbursement_amount": 1000, "disbursement_date": "2026-03-02"}]
    fec = Fec(FakeHttp({"https://api.open.fec.gov": {"results": rows, "pagination": {}}}), api_key="x")
    out = fec.disbursements("C0", AS_OF, cycles=1)
    assert [r["recipient"] for r in out] == ["SMITH FOR CONGRESS"]


def _lda_row(year, period, posted, codes=("EDU",), desc="H.R. 1234 support"):
    return {"filing_uuid": f"{year}-{period}", "filing_year": year, "filing_period": period, "filing_type": "Q", "income": "10000",
            "expenses": None, "dt_posted": posted, "client": {"name": "T"}, "registrant": {"name": "FIRM"},
            "lobbying_activities": [{"general_issue_code": c, "description": desc, "government_entities": [{"name": "SENATE"}],
                                     "lobbyists": [{}]} for c in codes], "affiliated_organizations": [], "foreign_entities": [],
            "filing_document_url": f"https://lda.example/{year}-{period}"}


def test_lda_point_in_time_and_bill_keys():
    rows = [_lda_row(2026, "second_quarter", "2026-07-20T10:00:00-04:00"), _lda_row(2026, "third_quarter", "2026-11-20T10:00:00-04:00")]
    lda = Lda(FakeHttp({"https://lda.senate.gov": lambda p: {"results": rows if p["filing_year"] == 2026 else [], "next": None}}))
    out = lda.filings(AS_OF, years=1, client_names=["T"])
    assert [r["quarter"] for r in out] == [2]
    assert out[0]["bills"] == ["H.R. 1234 (119th)"]
    assert _bills("8 U.S. 5 and U.S.C. 1101", 2026) == []


def test_form_990_respects_filing_lag():
    data = {"organization": {"name": "T"}, "filings_with_data": [
        {"tax_prd": 202606, "totrevenue": 1}, {"tax_prd": 202512, "totrevenue": 2}]}
    pp = ProPublica(FakeHttp({"https://projects.propublica.org": data}))
    assert [r["period_end"].month for r in pp.filings(1, AS_OF)] == [12]


def test_research_point_in_time(tmp_path):
    doc = {"entity_slug": "t", "researched_at": "2026-11-01T00:00:00Z", "agent_id": "a", "findings": [
        {"claim": "old", "dimension": "social", "pathway": "membership_base", "source_url": "https://a.org/1",
         "evidence_type": "verified", "direction": "weakens", "published_date": "2026-10-01"},
        {"claim": "future", "dimension": "social", "pathway": "membership_base", "source_url": "https://a.org/2",
         "evidence_type": "verified", "direction": "weakens", "published_date": "2026-11-05"}]}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(doc))
    assert [f.claim for f in load_research(p, date(2026, 11, 2)).findings] == ["old"]
    assert load_research(p, date(2026, 10, 31)) is None


def test_same_domain_counts_once():
    evs = [Evidence(provider="research-agent", claim=f"c{i}", source_url=f"https://www.news.com/{i}", direction=Direction.WEAKENS)
           for i in range(5)]
    assert pathways.independent(evs) == 1


def test_enacted_bill_is_a_result_not_a_forecast():
    ds = demo.dataset(AS_OF)
    key = "H.R. 1234 (119th)"
    for r in ds.lda:
        r["bills"] = [key] if r["bills"] else []
        for a in r["activities"]:
            a["bills"] = [key] if a["bills"] else []
    ds.bills[key] = {"key": key, "title": "Synthetic Act", "latest_action": "Became Public Law", "latest_action_date": date(2026, 9, 1),
                     "enacted": True, "public_law": "119-1", "url": "https://www.congress.gov/x"}
    assert not [c for c in sponsorship.candidates(ds) if c.kind == "named_bill"]
    assert sponsorship.recent_wins(ds)[0]["public_law"] == "119-1"


def test_pending_companion_of_enacted_bill_is_superseded():
    ds = demo.dataset(AS_OF)
    ds.bills["H.R. 1234 (119th)"] = {"key": "H.R. 1234 (119th)", "title": "Synthetic Schools Act of 2025", "latest_action": "Referred",
                                     "latest_action_date": date(2025, 5, 1), "enacted": False, "public_law": None, "url": "u"}
    ds.bills["H.R. 9 (119th)"] = {"key": "H.R. 9 (119th)", "title": "21st Century Synthetic Schools Act", "latest_action": "Became Public Law",
                                  "latest_action_date": date(2026, 7, 1), "enacted": True, "public_law": "119-9", "url": "u"}
    assert sponsorship.superseded_by(ds, "H.R. 1234 (119th)") == "H.R. 9 (119th)"
    assert not [c for c in sponsorship.candidates(ds) if c.label.startswith("H.R. 1234")]


def test_ach_tie_is_reported_not_broken():
    ds = demo.dataset(AS_OF)
    a = analysis.ach(ds, pathways.assess(ds))
    if a["tied"]:
        assert a["leading"] is None and "Tie" in a["note"]
    else:
        assert a["leading"] in analysis.POSTURES


def test_research_schema_rejects_bad_codes(tmp_path):
    import pytest
    from influence_intel.models import ResearchDoc
    with pytest.raises(Exception):
        ResearchDoc.model_validate({"entity_slug": "t", "researched_at": datetime.now(timezone.utc).isoformat(), "agent_id": "a",
                                    "initiatives": [{"name": "x", "kind": "coalition", "issue_code": "XXX", "stage": "announced",
                                                     "source_url": "https://a.org", "evidence_type": "verified"}]})
