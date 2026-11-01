"""Validated normalized contracts for TinyFish Agent career investigations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpportunityEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=4000)
    evidence_url: str = Field(min_length=8, max_length=2048)
    evidence_text: str = Field(min_length=1, max_length=2000)
    confidence: Literal["low", "medium", "high"]

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value):
        return value.lower().strip() if isinstance(value, str) else value


class AgentOpportunity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=512)
    employment_type: str | None = None
    experience_level: str | None = None
    location: str | None = None
    remote_status: str | None = None
    description: str | None = Field(default=None, max_length=12000)
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    preferred_skills: list[str] = Field(default_factory=list, max_length=50)
    eligibility: str | None = Field(default=None, max_length=4000)
    education_requirements: str | None = Field(default=None, max_length=2000)
    graduation_year: str | None = Field(default=None, max_length=128)
    salary: str | None = Field(default=None, max_length=512)
    application_deadline: str | None = Field(default=None, max_length=128)
    job_url: str = Field(min_length=8, max_length=2048)
    application_url: str | None = Field(default=None, max_length=2048)
    listing_status: Literal["active", "expired", "closed", "unknown"] = "unknown"
    evidence: list[OpportunityEvidence] = Field(default_factory=list, max_length=100)
    missing_fields: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("listing_status", mode="before")
    @classmethod
    def normalize_listing_status(cls, value):
        return value.lower().strip() if isinstance(value, str) else value

    @field_validator("required_skills", "preferred_skills", "missing_fields")
    @classmethod
    def trim_list_values(cls, values: list[str]) -> list[str]:
        return [item.strip()[:256] for item in values if item.strip()]


class AgentInvestigation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company_name: str | None = Field(default=None, max_length=512)
    jobs: list[AgentOpportunity] = Field(default_factory=list, max_length=15)
    execution_status: Literal["completed", "partial", "failed"]
    errors: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("execution_status", mode="before")
    @classmethod
    def normalize_execution_status(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip().lower()
        # Some completed provider runs place a short explanation after the
        # enum value despite the output schema. Accept only a recognized
        # leading enum token; Pydantic still rejects all other values.
        parts = value.split(maxsplit=1)
        if not parts:
            return value
        token = parts[0].rstrip(".,:;")
        return token if token in {"completed", "partial", "failed"} else value


# Deliberately use only basic JSON Schema keywords supported by the Agent API.
# Nullable values are represented as strings whose empty value is normalized to null.
AGENT_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "employment_type": {"type": "string"},
                    "experience_level": {"type": "string"},
                    "location": {"type": "string"},
                    "remote_status": {"type": "string"},
                    "description": {"type": "string"},
                    "required_skills": {"type": "array", "items": {"type": "string"}},
                    "preferred_skills": {"type": "array", "items": {"type": "string"}},
                    "eligibility": {"type": "string"},
                    "education_requirements": {"type": "string"},
                    "graduation_year": {"type": "string"},
                    "salary": {"type": "string"},
                    "application_deadline": {"type": "string"},
                    "job_url": {"type": "string"},
                    "application_url": {"type": "string"},
                    "listing_status": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "value": {"type": "string"},
                                "evidence_url": {"type": "string"},
                                "evidence_text": {"type": "string"},
                                "confidence": {"type": "string"},
                            },
                            "required": [
                                "field",
                                "value",
                                "evidence_url",
                                "evidence_text",
                                "confidence",
                            ],
                        },
                    },
                    "missing_fields": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "job_url", "listing_status", "evidence", "missing_fields"],
            },
        },
        "execution_status": {"type": "string"},
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["jobs", "execution_status", "errors"],
}
