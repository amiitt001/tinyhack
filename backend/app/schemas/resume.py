from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Education(BaseModel):
    institution: str | None = None
    qualification: str | None = None
    field: str | None = None
    dates: str | None = None


class Experience(BaseModel):
    organization: str | None = None
    role: str | None = None
    description: str | None = None
    dates: str | None = None


class ParsedResume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    internships: list[Experience] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    parsed_data: ParsedResume | None
    parse_error: str | None
    created_at: datetime
    updated_at: datetime
