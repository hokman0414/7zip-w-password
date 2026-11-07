"""Next-sponsorship outlook: ranks where the organization is likely to put money, advocacy and public backing next.

The score measures continuity of revealed behaviour (what it has actually lobbied for, funded and announced) plus
independent corroboration. It is a 0-100 ranking index, not a probability that any sponsorship occurs."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta

from .collect import Dataset, lda_quarters, latest_qkey
from .models import LDA_ISSUES, EvidenceType, SponsorshipCandidate

def _core_title(t: str | None) -> str:
    t = re.sub(r"\bof \d{4}\b|\b\d+(st|nd|rd|th) century\b", " ", (t or "").lower())
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", t).split())


def superseded_by(ds: Dataset, key: str) -> str | None:
    """A pending bill whose core title matches an enacted bill was most likely folded into that law."""
    st = ds.bills.get(key)
    core = _core_title(st and st.get("title"))
    if not core or len(core) < 12:
        return None
    for k, b in ds.bills.items():
        if k != key and b.get("enacted") and _core_title(b.get("title")) == core:
            return k
    return None


WEIGHTS = {"persistence": 0.35, "recency": 0.25, "momentum": 0.20, "corroboration": 0.20}
TYPE_WEIGHT = {EvidenceType.VERIFIED: 1.0, EvidenceType.REPORTED: 0.6, EvidenceType.ANALYST_JUDGMENT: 0.3}
STAGE_WEIGHT = {"announced": 1.0, "planned": 0.8, "ongoing": 0.7, "reported_considering": 0.4, "completed": 0.0}


def _score(c: dict[str, float]) -> float:
    return round(100 * sum(WEIGHTS[k] * min(max(c.get(k, 0.0), 0.0), 1.0) for k in WEIGHTS), 1)


def _qlabel(k: int) -> str:
    return f"{k // 4} Q{k % 4 + 1}"


def candidates(ds: Dataset, limit: int = 15, max_recipients: int = 3) -> list[SponsorshipCandidate]:
    q = lda_quarters(ds)
    L = latest_qkey(ds)
    research = ds.research
    inits = list(enumerate(research.initiatives)) if research else []
    windows = research.policy_windows if research else []
    out: list[SponsorshipCandidate] = []

    issue_q: dict[str, set[int]] = defaultdict(set)
    issue_ev: dict[str, list[str]] = defaultdict(list)
    for k, rows in q.items():
        for r in rows:
            for c in r["issue_codes"]:
                issue_q[c].add(k)
                issue_ev[c].append(r["evidence_id"])
    for code, ks in issue_q.items():
        last8 = {k for k in ks if L - 7 <= k <= L}
        if not last8:
            continue
        n4, np_ = len({k for k in last8 if k > L - 4}), len({k for k in last8 if k <= L - 4})
        recent = max(last8)
        matched = [(n, i) for n, i in inits if i.issue_code == code and STAGE_WEIGHT[i.stage] > 0]
        wins = [w for w in windows if w.issue_code == code and (w.date is None or w.date >= ds.as_of)]
        providers = ["senate-lda"] + (["research-initiative"] if matched else []) + (["policy-calendar"] if wins else [])
        comp = {"persistence": len(last8) / 8, "recency": 1.0 if recent >= L else 0.5 if recent >= L - 1 else 0.0,
                "momentum": 1.0 if n4 > np_ else 0.5 if n4 == np_ else 0.0, "corroboration": (len(providers) - 1) / 2}
        basis = [f"lobbied in {len(last8)}/8 recent quarters (latest {_qlabel(recent)})"]
        basis += [f"announced/planned: {i.name}" for _, i in matched[:3]]
        basis += [f"upcoming: {w.title} ({w.jurisdiction}, {w.stage}{', ' + str(w.date) if w.date else ''})" for w in wins[:3]]
        out.append(SponsorshipCandidate(
            label=f"{LDA_ISSUES.get(code, code)} advocacy", kind="issue_area", score=_score(comp), components=comp, basis=basis,
            providers=providers, evidence_ids=sorted(set(issue_ev[code]))[:12] + [ds.initiative_ev[n] for n, _ in matched],
            signposts=[f"Next LD-2 (quarter {_qlabel(L + 1)}) lists {code}", *(f"{w.title} reaches next stage" for w in wins[:2])]))

    bill_q: dict[str, set[int]] = defaultdict(set)
    bill_ev: dict[str, list[str]] = defaultdict(list)
    bill_codes: dict[str, set[str]] = defaultdict(set)
    for k, rows in q.items():
        for r in rows:
            for a in r["activities"]:
                for b in a["bills"]:
                    bill_q[b].add(k)
                    bill_ev[b].append(r["evidence_id"])
                    if a["code"]:
                        bill_codes[b].add(a["code"])
    for bill, ks in bill_q.items():
        last4 = {k for k in ks if L - 3 <= k <= L}
        if not last4:
            continue
        st = ds.bills.get(bill)
        if (st and st["enacted"]) or superseded_by(ds, bill):
            continue
        recent = max(last4)
        active = bool(st and st["latest_action_date"] and (ds.as_of - st["latest_action_date"]).days <= 120)
        comp = {"persistence": len(last4) / 4, "recency": 1.0 if recent >= L else 0.5 if recent >= L - 1 else 0.0,
                "momentum": 1.0 if min(ks) >= L - 1 else 0.5, "corroboration": 0.5 if active else 0.0}
        basis = [f"named in {len(last4)}/4 recent quarterly filings (latest {_qlabel(recent)})"]
        if st and st["latest_action"]:
            basis.append(f"latest action {st['latest_action_date']}: {st['latest_action'][:90]}")
        elif not st:
            basis.append("bill status not checked")
        ev = sorted(set(bill_ev[bill]))[:8] + ([st["evidence_id"]] if st and st.get("evidence_id") else [])
        out.append(SponsorshipCandidate(
            label=f"{bill} ({', '.join(LDA_ISSUES.get(c, c) for c in sorted(bill_codes[bill]))})"
                  + (f": {st['title'][:70]}" if st and st.get("title") else ""),
            kind="named_bill", score=_score(comp), components=comp, basis=basis,
            providers=["senate-lda"] + (["congress-gov"] if active else []), evidence_ids=ev,
            signposts=[f"{bill} committee markup, floor vote or companion bill", f"{bill} still named in next LD-2"]))

    by_recipient: dict[str, list[dict]] = defaultdict(list)
    for r in ds.fec:
        by_recipient[r["recipient_committee_id"] or r["recipient"]].append(r)
    cur = ds.as_of.year + (ds.as_of.year % 2)
    top = sorted(by_recipient.items(), key=lambda kv: -sum(r["amount"] for r in kv[1]))[:max_recipients]
    for key, rows in top:
        last = max(r["date"] for r in rows)
        cycles = {r["cycle"] for r in rows}
        total = sum(r["amount"] for r in rows)
        comp = {"persistence": len(cycles) / 2, "recency": 1.0 if (ds.as_of - last).days <= 180 else 0.5 if (ds.as_of - last).days <= 365 else 0.0,
                "momentum": 1.0 if cur in cycles else 0.0, "corroboration": 0.0}
        out.append(SponsorshipCandidate(
            label=f"{rows[0]['recipient']} (recipient committee)", kind="electoral_recipient", score=_score(comp), components=comp,
            basis=[f"${total:,.0f} across {len(rows)} disbursements; last {last}"], providers=["fec"],
            evidence_ids=[r["evidence_id"] for r in rows][:8], signposts=["Recipient appears in the next FEC periodic report"]))

    issue_labels = {c.label for c in out if c.kind == "issue_area"}
    for n, i in inits:
        sw = STAGE_WEIGHT[i.stage]
        if sw == 0 or (i.issue_code and f"{LDA_ISSUES[i.issue_code]} advocacy" in issue_labels):
            continue
        soon = i.expected_date and ds.as_of <= i.expected_date <= ds.as_of + timedelta(days=365)
        comp = {"persistence": 0.0, "recency": sw, "momentum": 1.0 if soon else 0.5, "corroboration": TYPE_WEIGHT[i.evidence_type]}
        out.append(SponsorshipCandidate(
            label=i.name, kind=i.kind, score=_score(comp), components=comp,
            basis=[f"{i.stage} ({i.evidence_type.value})" + (f"; expected {i.expected_date} ({i.date_confidence})" if i.expected_date else "")],
            providers=["research-initiative"], evidence_ids=[ds.initiative_ev[n]],
            signposts=[f"Public launch, budget line or partner announcement for {i.name}"]))
    return sorted(out, key=lambda c: (-c.score, c.kind != "issue_area", c.label))[:limit]


def recent_wins(ds: Dataset) -> list[dict]:
    """Lobbied bills (last 4 quarters) that became law on or before as_of: realized outcomes, not forecasts."""
    L = latest_qkey(ds)
    lobbied = {b for r in ds.lda if r["qkey"] >= L - 3 for b in r["bills"]}
    out = []
    for k, b in sorted(ds.bills.items()):
        if k in lobbied and b["enacted"]:
            related = sorted(x for x in lobbied if superseded_by(ds, x) == k)
            out.append({"bill": k, "title": b["title"], "public_law": b["public_law"], "date": str(b["latest_action_date"]),
                        "url": b["url"], "superseded_companions": related})
    return out
