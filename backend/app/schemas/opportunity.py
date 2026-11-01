"""Pydantic schemas for the opportunity discovery API.

All request schemas validate and bound user input.
All response schemas use ``from_attributes=True`` for ORM mapping.
Status values are stable strings (not enums) for forward compatibility.

Discovery run statuses:
    pending | running | completed | partially_completed | failed | cancelled

Opportunity extraction statuses:
    unextracted | extracted | failed | unsupported

Opportunity statuses:
    unknown | active | expired | removed

Source validation statuses:
    pending | accepted | rejected_validation | rejected_domain | rejected_url | error
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

_ALLOWED_EMPLOYMENT_TYPES = {"fulltime", "parttime", "internship", "contract"}
_ALLOWED_EXPERIENCE_LEVELS = {"fresher", "junior", "mid", "senior", "lead", "any"}
_ALLOWED_SOURCE_KEYS = {
    "official_company_careers",
    "linkedin_jobs",
    "internshala",
    "naukri",
    "wellfound",
}

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateDiscoveryRequest(BaseModel):
    """Request body for POST /api/v1/opportunity-discoveries."""

    query: str = Field(..., min_length=1, max_length=512, description="Job search query")
    location: str | None = Field(None, max_length=255, description="Location filter")
    employment_type: str | None = Field(
        None, description="Employment type: fulltime | parttime | internship | contract"
    )
    experience_level: str | None = Field(
        None, description="Experience level: fresher | junior | mid | senior | lead | any"
    )
    skills: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Skills to include in search",
    )
    sources: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Requested source keys",
    )
    idempotency_key: str | None = Field(
        None, max_length=255, description="Client-supplied idempotency key"
    )
    refresh: bool = Field(default=False, description="Bypass successful Agent result cache")

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_EMPLOYMENT_TYPES:
            raise ValueError(
                f"employment_type must be one of: {', '.join(sorted(_ALLOWED_EMPLOYMENT_TYPES))}"
            )
        return v

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_EXPERIENCE_LEVELS:
            raise ValueError(
                f"experience_level must be one of: {', '.join(sorted(_ALLOWED_EXPERIENCE_LEVELS))}"
            )
        return v

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[str]) -> list[str]:
        unknown = set(v) - _ALLOWED_SOURCE_KEYS
        if unknown:
            raise ValueError(f"Unknown source keys: {', '.join(sorted(unknown))}")
        return v

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str]) -> list[str]:
        return [s.strip()[:128] for s in v if s.strip()]

    @model_validator(mode="after")
    def sanitise_query(self) -> CreateDiscoveryRequest:
        # Strip leading/trailing whitespace from query.
        self.query = self.query.strip()
        if not self.query:
            raise ValueError("query must not be blank")
        return self


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class DiscoveryRunResponse(BaseModel):
    """Response for discovery run create and status endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    status: str
    query: str
    location: str | None
    employment_type: str | None
    experience_level: str | None
    refresh_requested: bool = False
    requested_sources: list | None
    requested_skills: list | None
    total_results: int | None
    accepted_results: int | None
    rejected_results: int | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    safe_error_message: str | None
    created_at: datetime
    updated_at: datetime


class OpportunityResponse(BaseModel):
    """Candidate result; unknown/unextracted records are not verified listings."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company_name: str | None
    description: str | None
    location: str | None
    work_mode: str | None
    employment_type: str | None
    experience_requirement: str | None
    required_skills: list | None
    preferred_skills: list | None
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    stipend: str | None
    application_url: str | None
    canonical_url: str | None
    source_url: str
    source_id: UUID | None
    status: str = Field(description="unknown means this search candidate is not listing-verified")
    extraction_status: str = Field(
        description="unextracted means only search-result metadata has been processed"
    )
    discovered_at: datetime
    last_verified_at: datetime | None
    evidence: list[OpportunityEvidenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_verified(self) -> bool:
        """Only detail-page extraction plus verification can mark a listing verified."""
        return (
            self.status == "active"
            and self.extraction_status == "extracted"
            and self.last_verified_at is not None
        )


class OpportunityEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    field_name: str
    field_value: str
    evidence_url: str
    evidence_text: str
    confidence: str
    observed_at: datetime


class TinyFishExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_url: str
    provider_run_id: str | None
    stage: str
    status: str
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    steps: int | None
    jobs_returned: int
    safe_error_code: str | None


class SavedOpportunityResponse(BaseModel):
    """Response for a saved opportunity association."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    opportunity_detail_id: UUID
    notes: str | None
    created_at: datetime
    opportunity: OpportunityResponse | None = None

    @model_validator(mode="before")
    @classmethod
    def embed_opportunity(cls, value):
        """Embed the related OpportunityDetail into the response."""
        if hasattr(value, "opportunity_detail") and value.opportunity_detail is not None:
            return {
                "id": value.id,
                "user_id": value.user_id,
                "opportunity_detail_id": value.opportunity_detail_id,
                "notes": value.notes,
                "created_at": value.created_at,
                "opportunity": value.opportunity_detail,
            }
        return value


class PaginatedOpportunityResponse(BaseModel):
    """Paginated list of opportunities."""

    items: list[OpportunityResponse]
    total: int
    limit: int
    offset: int


class PaginatedSavedOpportunityResponse(BaseModel):
    """Paginated list of saved opportunities."""

    items: list[SavedOpportunityResponse]
    total: int
    limit: int
    offset: int


class SaveRequest(BaseModel):
    """Optional body for save endpoint."""

    notes: str | None = Field(None, max_length=2048)


class SourceInfoResponse(BaseModel):
    """Public information about a registered source."""

    key: str
    display_name: str
    status: str
    supported_behavior: str
    reason: str | None
