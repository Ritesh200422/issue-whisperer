#!/usr/bin/env python
"""CLI script to build local FAISS vector index from cached GitHub issues."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import click
import numpy as np
from dotenv import load_dotenv

from models.issue import IssueModel
from tools.embedding_index import EmbeddingIndex
from tools.embedding_model import EmbeddingModel
from logging_config import setup_logging

load_dotenv()
setup_logging("INFO")


@click.command()
@click.option("--device", default=None, help="Device to use for embedding model ('cpu' or 'cuda').")
def main(device: str | None) -> None:
    """Build local FAISS index from data/cache/issues.json."""
    config_file = backend_dir / "config" / "config.yaml"
    click.echo(f"Building vector index using configuration from {config_file}")
    
    # 1. Read cached issues
    cache_path = Path("data/cache/issues.json")
    if not cache_path.exists():
        click.echo(f"Error: Cache file not found at {cache_path}. Run fetch_data.py first.", err=True)
        sys.exit(1)
        
    with open(cache_path, "r", encoding="utf-8") as f:
        issues_raw = json.load(f)
        
    issues = [IssueModel(**item) for item in issues_raw]
    if not issues:
        click.echo("Error: No issues found in cache.", err=True)
        sys.exit(1)
        
    click.echo(f"Loaded {len(issues)} issues from cache.")

    # 2. Setup embedding model
    embedding_model = EmbeddingModel(device=device)
    
    # 3. Generate embeddings
    click.echo("Generating embeddings for issues (this may take a moment)...")
    texts = [f"Title: {issue.title}\nBody: {issue.body or ''}" for issue in issues]
    
    try:
        embeddings = embedding_model.encode(texts, batch_size=32)
        click.echo(f"Generated embeddings shape: {embeddings.shape}")
        
        # 4. Build and save index
        index = EmbeddingIndex()
        index.build(embeddings, issues)
        click.echo("[OK] Local FAISS index and metadata successfully built and saved to 'data/index/'!")
    except Exception as e:
        click.echo(f"\n[Error] Failed to build index: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
