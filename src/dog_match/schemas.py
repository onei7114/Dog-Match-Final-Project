"""Typed public API response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    breed_name: str = Field(min_length=1)
    similarity_percent: int = Field(ge=1, le=100)
    reference_image_url: str = Field(min_length=1)
    disclaimer: str = Field(min_length=1)


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    breed_count: int = Field(ge=0)
    reference_image_count: int = Field(ge=0)


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
