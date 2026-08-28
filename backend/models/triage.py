"""Pydantic model representing structured Triage decisions."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class TriageModel(BaseModel):
    label: str = Field(description="Suggested category label for the issue (e.g. bug, feature, question, docs).")
    is_duplicate: bool = Field(description="Boolean flag indicating whether the issue is a duplicate of a historical candidate.")
    duplicate_of: int | None = Field(default=None, description="The integer issue number of the duplicate candidate. Must be null if is_duplicate is false.")
    confidence: float = Field(description="Confidence score of the duplicate claim, must be between 0.0 and 1.0.")
    evidence_quote: str | None = Field(default=None, description="Literal quote of evidence from the candidate issue supporting duplicate claim. Must be null if is_duplicate is false.")
    draft_reply: str = Field(description="A clean, friendly, professional reply draft to be posted to the new issue.")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @field_validator("duplicate_of")
    @classmethod
    def validate_duplicate_of(cls, v: int | None, info) -> int | None:
        is_dup = info.data.get("is_duplicate", False)
        if is_dup and v is None:
            raise ValueError("duplicate_of must not be null if is_duplicate is true")
        if not is_dup and v is not None:
            raise ValueError("duplicate_of must be null if is_duplicate is false")
        return v
