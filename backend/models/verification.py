"""Pydantic model representing structured Verification decisions."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class VerificationModel(BaseModel):
    status: str = Field(description="Verification status result: confirmed, possibly_related, or not_duplicate.")
    reason: str = Field(description="Detailed reason explaining the classification decision.")
    evidence_quote: str | None = Field(default=None, description="Literal segment of evidence quoted directly from candidate issue text.")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"confirmed", "possibly_related", "not_duplicate"}
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
