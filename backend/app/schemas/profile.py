from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    summary: str | None = Field(default=None, max_length=5000)
    career_stage: str | None = Field(default=None, max_length=64)
    completion_percent: int = Field(default=0, ge=0, le=100)


class ProfileResponse(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    id: str
    email: str | None
    status: str
