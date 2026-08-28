"""Pydantic models for GitHub Issues and Repository information."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class IssueModel(BaseModel):
    number: int
    title: str
    body: str | None = ""
    labels: list[str] = Field(default_factory=list)
    state: str = "open"  # "open" or "closed"
    created_at: str | None = None
    updated_at: str | None = None
    html_url: str | None = None
    user_login: str | None = None


class RepositoryModel(BaseModel):
    owner: str
    name: str
    description: str | None = ""
    stars: int = 0
    forks: int = 0
    open_issues_count: int = 0
    language: str | None = None
    readme_content: str | None = ""
