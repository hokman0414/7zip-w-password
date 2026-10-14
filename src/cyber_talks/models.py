from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Conference(BaseModel):
    id: str
    name: str
    country: str = "UNKNOWN"
    city: str | None = None
    youtube: list[str] = Field(default_factory=list)
    search: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    years: list[int] = Field(default_factory=list)


class TopicMatch(BaseModel):
    topic: str
    weight: int
    matched_terms: list[str]


class TalkCandidate(BaseModel):
    video_id: str
    title: str
    url: str
    description: str = ""
    channel: str = ""
    channel_id: str = ""
    upload_date: str | None = None  # YYYYMMDD
    duration_seconds: int | None = None
    view_count: int | None = None
    conference_id: str | None = None
    conference_name: str | None = None
    discovery_method: str = "unknown"
    topics: list[TopicMatch] = Field(default_factory=list)
    score: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def upload_datetime(self) -> datetime | None:
        if not self.upload_date or len(self.upload_date) < 8:
            return None
        try:
            return datetime.strptime(self.upload_date[:8], "%Y%m%d")
        except ValueError:
            return None


class SpeakerAttribution(BaseModel):
    name: str | None = None
    affiliation: str | None = None
    raw_credit: str | None = None


class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str


class TalkRecord(BaseModel):
    video_id: str
    title: str
    url: str
    description: str = ""
    channel: str = ""
    channel_id: str = ""
    upload_date: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    conference_id: str | None = None
    conference_name: str | None = None
    discovery_method: str = "unknown"
    topics: list[TopicMatch] = Field(default_factory=list)
    score: float = 0.0
    speakers: list[SpeakerAttribution] = Field(default_factory=list)
    transcript_language: str | None = None
    transcript_source: str | None = None  # manual | auto | none
    transcript_text: str = ""
    transcript_segments: list[TranscriptSegment] = Field(default_factory=list)
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    attribution: dict[str, Any] = Field(default_factory=dict)
