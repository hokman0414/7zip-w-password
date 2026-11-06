"""SQLite persistence: runs, company reports (full JSON + indexed columns), assignment votes, evidence, alerts."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import CompanyReport

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT, as_of TEXT, kind TEXT, tickers INTEGER, notes TEXT
);
CREATE TABLE IF NOT EXISTS reports (
    run_id TEXT, ticker TEXT, as_of TEXT, status TEXT, price REAL, price_time TEXT, discovery_score REAL,
    yes INTEGER, independent_yes INTEGER, no INTEGER, unknown INTEGER, passes_gate INTEGER, state_hash TEXT,
    report_json TEXT, PRIMARY KEY (run_id, ticker)
);
CREATE INDEX IF NOT EXISTS ix_reports_ticker ON reports(ticker, as_of);
CREATE TABLE IF NOT EXISTS assignment_votes (
    run_id TEXT, ticker TEXT, assignment_id INTEGER, grp TEXT, vote TEXT, confidence REAL, executor TEXT,
    input_fingerprint TEXT, dependent_on INTEGER, finding TEXT, PRIMARY KEY (run_id, ticker, assignment_id)
);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY, ticker TEXT, claim TEXT, source_url TEXT, published_date TEXT, retrieved_at TEXT,
    evidence_type TEXT, provider TEXT, sentiment TEXT, dimension TEXT
);
CREATE TABLE IF NOT EXISTS alerts (
    alert_key TEXT PRIMARY KEY, run_id TEXT, ticker TEXT, created_at TEXT, kind TEXT, message TEXT
);
CREATE TABLE IF NOT EXISTS proposals (
    run_id TEXT, created_at TEXT, symbol TEXT, side TEXT, quantity REAL, order_type TEXT, rationale TEXT,
    status TEXT, payload_json TEXT
);
"""


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def start_run(self, run_id: str, started_at: str, as_of: str, kind: str, n: int) -> None:
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?)", (run_id, started_at, None, as_of, kind, n, ""))

    def finish_run(self, run_id: str, finished_at: str, notes: str = "") -> None:
        with self.conn() as c:
            c.execute("UPDATE runs SET finished_at=?, notes=? WHERE run_id=?", (finished_at, notes, run_id))

    def save_report(self, r: CompanyReport, state_hash: str) -> None:
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                r.run_id, r.ticker, r.as_of.isoformat(), r.status.value, r.price,
                r.price_time.isoformat() if r.price_time else None, r.discovery_score, r.tally.yes,
                r.tally.independent_yes, r.tally.no, r.tally.unknown, int(r.tally.passes_gate), state_hash,
                r.model_dump_json()))
            c.executemany("INSERT OR REPLACE INTO assignment_votes VALUES (?,?,?,?,?,?,?,?,?,?)", [
                (r.run_id, r.ticker, a.assignment_id, a.group, a.vote.value, a.confidence, a.executor,
                 a.input_fingerprint, a.dependent_on, a.finding) for a in r.assignments])
            c.executemany("INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?)", [
                (e.id if not e.id.startswith(("mkt:", "val:")) else f"{e.id}:{r.run_id}", e.ticker, e.claim, e.source_url,
                 str(e.published_date) if e.published_date else None, e.retrieved_at.isoformat(), e.evidence_type.value,
                 e.provider, e.sentiment.value, e.dimension) for e in r.evidence])

    def previous_report(self, ticker: str, before_run: str) -> CompanyReport | None:
        with self.conn() as c:
            row = c.execute(
                "SELECT report_json FROM reports WHERE ticker=? AND run_id<>? ORDER BY as_of DESC LIMIT 1",
                (ticker, before_run)).fetchone()
        return CompanyReport.model_validate_json(row["report_json"]) if row else None

    def latest_reports(self) -> list[CompanyReport]:
        with self.conn() as c:
            row = c.execute("SELECT run_id FROM runs WHERE finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1").fetchone()
            if not row:
                return []
            rows = c.execute("SELECT report_json FROM reports WHERE run_id=?", (row["run_id"],)).fetchall()
        return [CompanyReport.model_validate_json(r["report_json"]) for r in rows]

    def history(self, ticker: str) -> list[dict]:
        with self.conn() as c:
            rows = c.execute("SELECT run_id, as_of, status, price, independent_yes, discovery_score FROM reports "
                             "WHERE ticker=? ORDER BY as_of", (ticker,)).fetchall()
        return [dict(r) for r in rows]

    def add_alert(self, key: str, run_id: str, ticker: str, created_at: str, kind: str, message: str) -> bool:
        with self.conn() as c:
            cur = c.execute("INSERT OR IGNORE INTO alerts VALUES (?,?,?,?,?,?)", (key, run_id, ticker, created_at, kind, message))
            return cur.rowcount == 1

    def alerts(self, limit: int = 100) -> list[dict]:
        with self.conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))]

    def save_proposals(self, run_id: str, created_at: str, proposals: list[dict]) -> None:
        with self.conn() as c:
            c.executemany("INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?)", [
                (run_id, created_at, p["symbol"], p["side"], p.get("quantity"), p.get("order_type", "limit"),
                 p["rationale"], p["status"], json.dumps(p, default=str)) for p in proposals])

    def proposals(self, run_id: str | None = None) -> list[dict]:
        with self.conn() as c:
            if run_id is None:
                row = c.execute("SELECT run_id FROM proposals ORDER BY created_at DESC LIMIT 1").fetchone()
                if not row:
                    return []
                run_id = row["run_id"]
            return [json.loads(r["payload_json"]) for r in c.execute("SELECT payload_json FROM proposals WHERE run_id=?", (run_id,))]
