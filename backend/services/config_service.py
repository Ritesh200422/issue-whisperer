"""Configuration service — loads config.yaml and validates with Pydantic."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "ollama"
    model: str = "gemma3:4b"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout: int = 120


class EmbeddingsConfig(BaseModel):
    model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    batch_size: int = 32


class RetrievalConfig(BaseModel):
    top_k: int = 3
    similarity_threshold: float = 0.3


class GitHubConfig(BaseModel):
    base_url: str = "https://api.github.com"
    cache_dir: str = "data/cache"
    use_cache: bool = True


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )


class AppConfig(BaseModel):
    name: str = "Issue Whisperer"
    version: str = "0.1.0"
    log_level: str = "INFO"


class DataConfig(BaseModel):
    cache_dir: str = "data/cache"
    index_dir: str = "data/index"


class TrajectoriesConfig(BaseModel):
    dir: str = "trajectories"
    enabled: bool = True


class PathsConfig(BaseModel):
    outputs: str = "outputs"


class Config(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    trajectories: TrajectoriesConfig = Field(default_factory=TrajectoriesConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)


@lru_cache(maxsize=1)
def get_config(config_path: str | None = None) -> Config:
    """Load config from YAML, then overlay environment variable overrides.

    Call ``get_config.cache_clear()`` in tests that need a fresh config.
    """
    if config_path is None:
        here = Path(__file__).parent.parent  # backend/
        config_path = str(here / "config" / "config.yaml")

    raw: dict[str, Any] = {}
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    # Overlay environment variables so secrets never live in config.yaml
    llm = raw.setdefault("llm", {})
    if os.environ.get("LLM_PROVIDER"):
        llm["provider"] = os.environ["LLM_PROVIDER"]
    if os.environ.get("LLM_MODEL"):
        llm["model"] = os.environ["LLM_MODEL"]
    if os.environ.get("LLM_BASE_URL"):
        llm["base_url"] = os.environ["LLM_BASE_URL"]
    if os.environ.get("LLM_API_KEY"):
        llm["api_key"] = os.environ["LLM_API_KEY"]

    embeddings = raw.setdefault("embeddings", {})
    if os.environ.get("EMBEDDING_DEVICE"):
        embeddings["device"] = os.environ["EMBEDDING_DEVICE"]

    # GITHUB_TOKEN is read directly from env by the GitHub client;
    # we store it in config so it flows through the same config object.
    github = raw.setdefault("github", {})
    if os.environ.get("GITHUB_TOKEN"):
        github["token"] = os.environ["GITHUB_TOKEN"]

    if os.environ.get("LOG_LEVEL"):
        raw.setdefault("app", {})["log_level"] = os.environ["LOG_LEVEL"]

    return Config(**raw)
