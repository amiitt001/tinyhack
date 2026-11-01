import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

RunStatus = Literal["pending", "running", "completed", "partially_completed", "failed", "cancelled"]
EmploymentType = Literal[
    "full_time", "part_time", "internship", "contract", "temporary", "volunteer", "other"
]


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    query: str = Field(min_length=2, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    employment_type: EmploymentType | None = None
    experience_level: str | None = Field(default=None, min_length=1, max_length=64)
    skills: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(
        default_factory=list, max_length=30
    )
    sources: list[str] = Field(
        default_factory=lambda: ["official_company_careers"], min_length=1, max_length=5
    )

    @field_validator("query", "location", "experience_level")
    @classmethod
    def plain_query(cls, value: str | None) -> str | None:
        if value and (
            re.search(r"[\x00-\x1f\x7f]|https?://|\b(?:site|filetype|inurl):", value, re.I)
        ):
            raise ValueError("Use plain search terms, not URLs or provider operators")
        return value

    @field_validator("skills", "sources")
    @classmethod
    def unique_values(cls, values: list[str]) -> list[str]:
        return sorted(set(values), key=str.casefold)


class DiscoveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    query: str
    location: str | None
    employment_type: str | None
    experience_level: str | None
    requested_sources: list[str]
    status: RunStatus
    total_results: int
    accepted_results: int
    rejected_results: int
    attempt_count: int
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    safe_error_message: str | None
    created_at: datetime
    updated_at: datetime


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_id: UUID
    original_url: str | None
    canonical_url: str | None
    observed_at: datetime
    validation_status: str


class OpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    company_name: str | None
    description: str | None
    location: str | None
    work_mode: str | None
    employment_type: str | None
    experience_requirement: str | None
    required_skills: list[str] | None
    preferred_skills: list[str] | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    salary_unit: str | None
    stipend: str | None
    application_url: str | None
    canonical_url: str | None
    source_url: str
    source_id: UUID | None
    source_external_id: str | None
    deadline: datetime | None
    discovered_at: datetime
    last_verified_at: datetime | None
    last_attempted_at: datetime | None
    expires_at: datetime | None
    status: str
    extraction_status: str | None
    content_hash: str | None
    sources: list[ObservationResponse] = Field(default_factory=list)


class OpportunityPage(BaseModel):
    items: list[OpportunityResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class SaveResponse(BaseModel):
    opportunity_id: UUID
    saved: bool


class SourceResponse(BaseModel):
    name: str
    status: Literal["configured", "supported", "enabled", "disabled", "restricted", "unavailable"]
    supported: bool
    configured: bool
    allowed_domains: tuple[str, ...]
    behavior: str
    attribution: str
    validation_policy: str
    access_restrictions: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class DiscoveryErrorResponse(BaseModel):
    # Preserve FastAPI's existing auth and request-validation shapes alongside domain errors.
    detail: ErrorDetail | str | list[dict]
