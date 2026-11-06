"""Read-only HTTP API over the latest persisted run. There is intentionally no endpoint that places orders."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .db import Store

app = FastAPI(title="Silent Stocks", description="Research output only. No order execution.")


def _store() -> Store:
    return Store(get_settings().db_path)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/companies")
def companies():
    return [{"ticker": r.ticker, "company": r.company, "status": r.status.value, "price": r.price,
             "independent_yes": r.tally.independent_yes, "yes": r.tally.yes, "no": r.tally.no, "unknown": r.tally.unknown,
             "discovery_score": r.discovery_score, "critical_vetoes": [v.code for v in r.vetoes if v.severity == "critical"],
             "as_of": r.as_of} for r in _store().latest_reports()]


@app.get("/companies/{ticker}")
def company(ticker: str):
    for r in _store().latest_reports():
        if r.ticker == ticker.upper():
            return r
    raise HTTPException(404, f"{ticker} not in latest run")


@app.get("/companies/{ticker}/history")
def history(ticker: str):
    return _store().history(ticker.upper())


@app.get("/alerts")
def alerts(limit: int = 100):
    return _store().alerts(limit)


@app.get("/proposals")
def proposals():
    return {"notice": "Proposals require human approval. This API cannot submit orders.", "proposals": _store().proposals()}
