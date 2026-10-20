"""Shared Pydantic models for evidence and case state."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Reliability(str, Enum):
    A = "A"  # completely reliable
    B = "B"  # usually reliable
    C = "C"  # fairly reliable
    D = "D"  # not usually reliable
    E = "E"  # unreliable
    F = "F"  # cannot be judged


class ClaimStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CORROBORATED = "CORROBORATED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    MISSING = "MISSING"


class EvidenceTier(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    HEARSAY = "hearsay"


class EvidenceRecord(BaseModel):
    evidence_id: str
    source_url: str
    source_title: str = ""
    collection_timestamp_utc: datetime = Field(default_factory=utc_now)
    publication_timestamp_utc: Optional[datetime] = None
    local_path: Optional[str] = None
    sha256: Optional[str] = None
    source_category: str
    reliability: Reliability = Reliability.F
    evidence_tier: EvidenceTier = EvidenceTier.SECONDARY
    independently_corroborates: list[str] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    extracted_facts: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class CaseConfig(BaseModel):
    case_id: str = "royale_diamonds"
    platform: str = "TikTok Shop"
    seller_display: str = "Royale Diamonds"
    seller_username_confirmed: Optional[str] = None
    purchase_date: str = "2026-10-19"
    winning_bid_usd: float = 350.0
    igi_report: str = "LG839637366"
    tracking_number: Optional[str] = None
    advertised: dict[str, Any] = Field(default_factory=dict)