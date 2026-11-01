from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CareerPath(BaseModel):
    title: str
    explanation: str
    strengths: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    learning_priorities: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class CareerAnalysisOutput(BaseModel):
    career_paths: list[CareerPath] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CareerAnalysisResponse(CareerAnalysisOutput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    resume_id: UUID | None
    model_version: str
    prompt_version: str
    status: str
    error: str | None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def unpack_persisted_output(cls, value):
        if hasattr(value, "output"):
            payload = dict(value.output or {})
            for field in (
                "id",
                "user_id",
                "resume_id",
                "model_version",
                "prompt_version",
                "status",
                "error",
                "created_at",
            ):
                payload[field] = getattr(value, field)
            return payload
        return value
