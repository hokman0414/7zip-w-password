"""Offline demo on SYNTHETIC fixtures. Every record is invented and labelled; nothing describes a real organization."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .collect import Sources, collect
from .models import Affiliate, EntityProfile, ResearchDoc

FIXTURE_URL = "https://example.invalid/synthetic/"


def profile() -> EntityProfile:
    return EntityProfile(
        slug="demo-synthetic-federation", name="Synthetic Faith Federation (DEMO)", tradition="synthetic",
        description="Invented organization used to exercise the pipeline offline.", news_query="synthetic faith federation",
        affiliates=[
            Affiliate(name="Synthetic Faith Federation (DEMO)", relation="core", lda_client_names=["SYNTHETIC FEDERATION"]),
            Affiliate(name="Synthetic Relief Services (DEMO)", relation="service", ein=1, usaspending_names=["Synthetic Relief"]),
            Affiliate(name="Synthetic Values PAC (DEMO)", relation="pac", fec_committee_ids=["C00000001"]),
        ])


class _Lda:
    def filings(self, as_of, years=3, client_names=(), registrant_names=()):
        out = []
        start = (as_of.year - 2) * 4
        plan = {"REL": range(0, 12), "EDU": range(0, 12), "IMM": range(4, 12), "HCR": range(0, 6), "TAX": range(9, 12)}
        for k in range(start, start + 12):
            y, q = divmod(k, 4)
            posted = date(y, 3 * q + 3, 28) + timedelta(days=22)
            if posted > as_of:
                continue
            codes = sorted(c for c, ks in plan.items() if (k - start) in ks)
            acts = [{"code": c, "description": f"Synthetic activity on {c}" + (" incl. H.R. 1234" if c == "EDU" and k - start >= 8 else ""),
                     "bills": ["H.R. 1234 (119th)"] if c == "EDU" and k - start >= 8 else [], "government_entities": ["HOUSE OF REPRESENTATIVES", "SENATE", "Education, Dept of"],
                     "lobbyist_count": 2} for c in codes]
            out.append({"uuid": f"demo-{k}", "year": y, "quarter": q + 1, "qkey": k, "filing_type": f"Q{q + 1}",
                        "amount": 40000.0 + 2500 * (k - start), "client": "SYNTHETIC FEDERATION", "registrant": "SYNTHETIC FEDERATION",
                        "in_house": True, "issue_codes": codes, "activities": acts,
                        "bills": ["H.R. 1234 (119th)"] if k - start >= 8 else [], "affiliated_organizations": ["Synthetic Schools Network (DEMO)"],
                        "foreign_entities": [], "url": f"{FIXTURE_URL}lda/{k}", "posted": posted})
        return out


class _ProPublica:
    def filings(self, ein, as_of):
        return [{"ein": ein, "name": "Synthetic Relief Services (DEMO)", "period_end": date(y, 12, 28), "year": y,
                 "revenue": 40e6 + 3e6 * (y - as_of.year), "expenses": 38e6 + 2e6 * (y - as_of.year), "assets": 90e6 + 4e6 * (y - as_of.year),
                 "contributions": 18e6, "form": 990, "url": f"{FIXTURE_URL}990/{y}"} for y in range(as_of.year - 4, as_of.year - 1)]


class _Fec:
    def disbursements(self, committee_id, as_of, cycles=2, max_pages=5):
        cur = as_of.year + (as_of.year % 2)
        return [{"committee_id": committee_id, "recipient": f"SYNTHETIC CANDIDATE COMMITTEE {n}", "recipient_committee_id": f"C0000010{n}",
                 "entity_type": "CCM", "amount": 2500.0, "date": as_of - timedelta(days=40 * n + 10), "purpose": "CONTRIBUTION",
                 "cycle": cur if n < 4 else cur - 2, "url": f"{FIXTURE_URL}fec/{n}"} for n in range(6)]


class _Awards:
    def search(self, name, as_of, lookback_days=1095, limit=25):
        return [{"kind": "grant", "award_id": f"DEMO-{n}", "recipient": "SYNTHETIC RELIEF SERVICES", "amount": 1.5e6,
                 "agency": ag, "start_date": as_of - timedelta(days=200 * n + 30), "description": "Synthetic refugee services grant",
                 "url": f"{FIXTURE_URL}award/{n}"} for n, ag in enumerate(["Department of State", "Department of Health and Human Services"])]


class _News:
    def summary(self, query, as_of):
        return {"query": query, "volume_recent_90d": 0.012, "volume_prior_90d": 0.009, "tone_recent_90d": -0.8,
                "tone_prior_90d": -1.4, "url": f"{FIXTURE_URL}gdelt"}


def research(as_of: date) -> ResearchDoc:
    u = FIXTURE_URL
    return ResearchDoc.model_validate({
        "entity_slug": "demo-synthetic-federation", "researched_at": datetime.combine(as_of, datetime.min.time(), timezone.utc),
        "agent_id": "demo-fixture",
        "findings": [
            {"claim": "Synthetic survey: adherents fell 4% over five years", "dimension": "social", "pathway": "membership_base",
             "source_url": u + "a.org/1", "evidence_type": "verified", "direction": "weakens", "published_date": str(as_of - timedelta(days=60))},
            {"claim": "Synthetic report: youth program enrollment doubled", "dimension": "social", "pathway": "membership_base",
             "source_url": u + "b.org/1", "evidence_type": "reported", "direction": "strengthens"},
            {"claim": "Synthetic: independent safeguarding audit published", "dimension": "social", "pathway": "institutional_trust",
             "source_url": u + "c.org/1", "evidence_type": "verified", "direction": "strengthens"},
            {"claim": "Synthetic: settlement over past misconduct claims", "dimension": "legal", "pathway": "institutional_trust",
             "source_url": u + "d.org/1", "evidence_type": "verified", "direction": "weakens"},
            {"claim": "Synthetic: streaming audience up 30%", "dimension": "technological", "pathway": "digital_reach",
             "source_url": u + "e.org/1", "evidence_type": "reported", "direction": "strengthens"},
            {"claim": "Synthetic: amicus brief filed in religious-liberty case", "dimension": "legal", "pathway": "legal_advocacy",
             "source_url": u + "f.org/1", "evidence_type": "verified", "direction": "strengthens"},
            {"claim": "Synthetic: partner churches in two conflict regions", "dimension": "military", "pathway": "transnational_network",
             "source_url": u + "g.org/1", "evidence_type": "verified", "direction": "strengthens", "region": "East Africa"},
        ],
        "initiatives": [
            {"name": "Synthetic school-choice coalition campaign", "kind": "coalition", "issue_code": "EDU", "stage": "announced",
             "source_url": u + "h.org/1", "evidence_type": "verified", "expected_date": str(as_of + timedelta(days=90)), "date_confidence": "estimated"},
            {"name": "Synthetic affordable housing on church land", "kind": "program", "issue_code": "HOU", "stage": "planned",
             "source_url": u + "i.org/1", "evidence_type": "reported"},
        ],
        "alliances": [{"partner": "Synthetic Interfaith Council", "kind": "interfaith", "source_url": u + "j.org/1", "evidence_type": "verified"}],
        "subgroups": [{"name": "Synthetic Relief Services (DEMO)", "kind": "service_institution", "role": "Runs the relief arm",
                       "issue_codes": ["HOU"], "pathways": ["institutional_services", "federal_partnerships"],
                       "source_url": u + "s.org/1", "evidence_type": "verified"}],
        "policy_windows": [{"title": "Synthetic education savings account bill", "jurisdiction": "US Congress", "stage": "committee",
                            "date": str(as_of + timedelta(days=45)), "issue_code": "EDU", "source_url": u + "k.org/1"}],
    })


def dataset(as_of: date):
    return collect(profile(), as_of, Sources(_Lda(), _ProPublica(), _Fec(), _Awards(), _News()), research(as_of))
