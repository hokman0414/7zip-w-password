from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_WATCHLIST = ["CODA", "PLPC", "MPTI", "TWIN", "TSSI", "RCAT", "AMPX", "EOSE", "ONDS", "KTOS"]

# Disclosed public companies from the federation record. Tracked for price trend only.
# A move here is not a research buy. LUMI is the Tel Aviv listing and may have no US quote.
TRACKED_COMPANIES = [
    {"symbol": "GS", "name": "Goldman Sachs", "role": "Dallas federation event sponsor"},
    {"symbol": "MMC", "name": "Marsh McLennan", "role": "Dallas federation gold sponsor"},
    {"symbol": "KR", "name": "Kroger", "role": "Cincinnati federation presenting partner"},
    {"symbol": "FCF", "name": "First Commonwealth", "role": "Cincinnati federation presenting partner"},
    {"symbol": "WTFC", "name": "Wintrust", "role": "Milwaukee Economic Forum sponsor"},
    {"symbol": "MCS", "name": "Marcus", "role": "Milwaukee VALOR sponsor"},
    {"symbol": "LUMI", "name": "Bank Leumi", "role": "Rebuild Israel reservist loan window, announced 2025-09-21"},
]
DRASTIC_MOVE_PCT = 0.05


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("SILENT_DATA_DIR", ROOT / "data")))
    db_path: Path = field(default_factory=lambda: Path(os.environ.get("SILENT_DB_PATH", ROOT / "data" / "silent_stocks.db")))
    reports_dir: Path = field(default_factory=lambda: Path(os.environ.get("SILENT_REPORTS_DIR", ROOT / "reports")))
    sec_user_agent: str = field(
        default_factory=lambda: os.environ.get("SEC_USER_AGENT", "SilentStocksResearch research@example.com")
    )
    timezone: str = field(default_factory=lambda: os.environ.get("SILENT_TIMEZONE", "America/New_York"))
    daily_run_hour: int = field(default_factory=lambda: int(os.environ.get("SILENT_DAILY_HOUR", "9")))
    # Weekend + holiday tolerance; older market data marks a company STALE DATA.
    stale_market_hours: float = field(default_factory=lambda: _env_float("SILENT_STALE_MARKET_HOURS", 96.0))
    stale_research_days: float = field(default_factory=lambda: _env_float("SILENT_STALE_RESEARCH_DAYS", 30.0))
    gate_yes_threshold: int = 80
    total_assignments: int = 100
    openai_api_key: str | None = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY"))
    anthropic_api_key: str | None = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY"))
    llm_model: str | None = field(default_factory=lambda: os.environ.get("SILENT_LLM_MODEL"))
    polygon_api_key: str | None = field(default_factory=lambda: os.environ.get("POLYGON_API_KEY"))
    demo_mode: bool = field(default_factory=lambda: os.environ.get("SILENT_DEMO", "0") == "1")

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def snapshot_dir(self) -> Path:
        return self.data_dir / "snapshots" / "robinhood"

    @property
    def findings_dir(self) -> Path:
        return self.data_dir / "research" / "agent_findings"

    @property
    def policy_events_path(self) -> Path:
        return self.data_dir / "research" / "policy" / "policy_events.json"

    @property
    def fixtures_dir(self) -> Path:
        return self.data_dir / "fixtures"


def get_settings() -> Settings:
    return Settings()
