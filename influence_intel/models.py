from __future__ import annotations

import datetime as _dt
import hashlib
from enum import Enum

from pydantic import BaseModel, Field, field_validator

DIMENSIONS = ["social", "technological", "economic", "military", "political", "legal", "environmental"]

LDA_ISSUES = {
    "ACC": "Accounting", "ADV": "Advertising", "AER": "Aerospace", "AGR": "Agriculture", "ALC": "Alcohol and Drug Abuse",
    "ANI": "Animals", "APP": "Apparel/Clothing Industry/Textiles", "ART": "Arts/Entertainment", "AUT": "Automotive Industry",
    "AVI": "Aviation/Airlines/Airports", "BAN": "Banking", "BNK": "Bankruptcy", "BEV": "Beverage Industry",
    "BUD": "Budget/Appropriations", "CIV": "Civil Rights/Civil Liberties", "CHM": "Chemicals/Chemical Industry",
    "CAW": "Clean Air and Water (quality)", "CDT": "Commodities (big ticket)", "COM": "Communications/Broadcasting/Radio/TV",
    "CPI": "Computer Industry", "CON": "Constitution", "CSP": "Consumer Issues/Safety/Products",
    "CPT": "Copyright/Patent/Trademark", "DEF": "Defense", "DIS": "Disaster Planning/Emergencies",
    "DOC": "District of Columbia", "ECN": "Economics/Economic Development", "EDU": "Education", "ENG": "Energy/Nuclear",
    "ENV": "Environment/Superfund", "FAM": "Family issues/Abortion/Adoption", "FIN": "Financial Institutions/Investments/Securities",
    "FIR": "Firearms/Guns/Ammunition", "FOO": "Food Industry (safety, labeling, etc.)", "FOR": "Foreign Relations",
    "FUE": "Fuel/Gas/Oil", "GAM": "Gaming/Gambling/Casino", "GOV": "Government Issues", "HCR": "Health Issues",
    "HOM": "Homeland Security", "HOU": "Housing", "IMM": "Immigration", "IND": "Indian/Native American Affairs",
    "INS": "Insurance", "INT": "Intelligence", "LBR": "Labor Issues/Antitrust/Workplace",
    "LAW": "Law Enforcement/Crime/Criminal Justice", "MAN": "Manufacturing", "MAR": "Marine/Maritime/Boating/Fisheries",
    "MIA": "Media (information/publishing)", "MED": "Medical/Disease Research/Clinical Labs", "MMM": "Medicare/Medicaid",
    "MON": "Minting/Money/Gold Standard", "NAT": "Natural Resources", "PHA": "Pharmacy", "POS": "Postal",
    "RRR": "Railroads", "RES": "Real Estate/Land Use/Conservation", "REL": "Religion", "RET": "Retirement",
    "ROD": "Roads/Highway", "SCI": "Science/Technology", "SMB": "Small Business", "SPO": "Sports/Athletics",
    "TAR": "Tariff (miscellaneous tariff bills)", "TAX": "Taxation/Internal Revenue Code", "TEC": "Telecommunications",
    "TOB": "Tobacco", "TOR": "Torts", "TRD": "Trade (domestic/foreign)", "TRA": "Transportation", "TOU": "Travel/Tourism",
    "TRU": "Trucking/Shipping", "URB": "Urban Development/Municipalities", "UNM": "Unemployment", "UTI": "Utilities",
    "VET": "Veterans", "WAS": "Waste (hazardous/solid/interstate/nuclear)", "WEL": "Welfare",
}


class EvidenceType(str, Enum):
    VERIFIED = "verified"
    REPORTED = "reported"
    ANALYST_JUDGMENT = "analyst_judgment"


class Direction(str, Enum):
    """Effect on the organization's capacity to sustain influence, not a moral judgment."""
    STRENGTHENS = "strengthens"
    WEAKENS = "weakens"
    NEUTRAL = "neutral"


class Evidence(BaseModel):
    id: str = ""
    provider: str
    claim: str
    source_url: str
    source_title: str = ""
    published_date: _dt.date | None = None
    retrieved_at: str | None = None
    evidence_type: EvidenceType = EvidenceType.VERIFIED
    direction: Direction = Direction.NEUTRAL
    dimension: str | None = None
    pathways: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    amount: float | None = None

    def model_post_init(self, _ctx) -> None:
        if not self.id:
            self.id = hashlib.sha256(f"{self.provider}|{self.source_url}|{self.claim}".encode()).hexdigest()[:16]


class Affiliate(BaseModel):
    name: str
    relation: str = "core"
    ein: int | None = None
    lda_client_names: list[str] = Field(default_factory=list)
    lda_registrant_names: list[str] = Field(default_factory=list)
    fec_committee_ids: list[str] = Field(default_factory=list)
    usaspending_names: list[str] = Field(default_factory=list)


class EntityProfile(BaseModel):
    slug: str
    name: str
    tradition: str | None = None
    description: str = ""
    home_country: str = "United States"
    news_query: str | None = None
    affiliates: list[Affiliate]
    is_church_exempt_from_lda: bool = True

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not v or not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("slug must be alphanumeric, '-' or '_'")
        return v


class ResearchFinding(BaseModel):
    claim: str
    dimension: str
    pathway: str
    source_url: str
    source_title: str = ""
    published_date: _dt.date | None = None
    evidence_type: EvidenceType
    direction: Direction
    region: str | None = None

    @field_validator("dimension")
    @classmethod
    def _dim(cls, v: str) -> str:
        if v not in DIMENSIONS:
            raise ValueError(f"dimension must be one of {DIMENSIONS}")
        return v


INITIATIVE_KINDS = ["legislation", "campaign_or_candidate", "program", "institution", "coalition", "media", "litigation",
                    "international", "other"]
INITIATIVE_STAGES = ["announced", "planned", "reported_considering", "ongoing", "completed"]


class Initiative(BaseModel):
    """A publicly announced or reported sponsorship, program, campaign or coalition the organization backs."""
    name: str
    kind: str
    issue_code: str | None = None
    stage: str
    expected_date: _dt.date | None = None
    date_confidence: str = "unknown"
    source_url: str
    source_title: str = ""
    published_date: _dt.date | None = None
    evidence_type: EvidenceType

    @field_validator("kind")
    @classmethod
    def _kind(cls, v: str) -> str:
        if v not in INITIATIVE_KINDS:
            raise ValueError(f"kind must be one of {INITIATIVE_KINDS}")
        return v

    @field_validator("stage")
    @classmethod
    def _stage(cls, v: str) -> str:
        if v not in INITIATIVE_STAGES:
            raise ValueError(f"stage must be one of {INITIATIVE_STAGES}")
        return v

    @field_validator("issue_code")
    @classmethod
    def _code(cls, v: str | None) -> str | None:
        if v is not None and v not in LDA_ISSUES:
            raise ValueError("issue_code must be an LDA general issue code")
        return v


class Alliance(BaseModel):
    partner: str
    kind: str
    since: _dt.date | None = None
    source_url: str
    evidence_type: EvidenceType


class PolicyWindow(BaseModel):
    title: str
    jurisdiction: str
    stage: str
    date: _dt.date | None = None
    issue_code: str | None = None
    source_url: str

    @field_validator("issue_code")
    @classmethod
    def _code(cls, v: str | None) -> str | None:
        if v is not None and v not in LDA_ISSUES:
            raise ValueError("issue_code must be an LDA general issue code")
        return v


class ResearchDoc(BaseModel):
    entity_slug: str
    researched_at: _dt.datetime
    agent_id: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    initiatives: list[Initiative] = Field(default_factory=list)
    alliances: list[Alliance] = Field(default_factory=list)
    policy_windows: list[PolicyWindow] = Field(default_factory=list)


class Check(BaseModel):
    id: str
    question: str
    result: bool | None
    detail: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class PathwayAssessment(BaseModel):
    id: str
    label: str
    dimension: str
    strength: float | None
    coverage: float
    trend: str
    pressures: list[str]
    checks: list[Check]
    modern_levers: list[str]


class SponsorshipCandidate(BaseModel):
    label: str
    kind: str
    score: float
    components: dict[str, float]
    basis: list[str]
    providers: list[str]
    evidence_ids: list[str]
    signposts: list[str]
