#!/usr/bin/env python
"""CLI script to fetch and cache GitHub repository data and issues."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import click
from dotenv import load_dotenv
from tools.github_client import GitHubClient
from logging_config import setup_logging

load_dotenv()
setup_logging("INFO")


@click.command()
@click.argument("repository")
@click.option("--limit", default=100, help="Maximum number of issues to fetch.")
def main(repository: str, limit: int) -> None:
    """Fetch repository info and issues from OWNER/REPO and save to cache.

    Example:
      python scripts/fetch_data.py pytorch/pytorch
    """
    if "/" not in repository:
        click.echo("Error: Repository must be in the format 'OWNER/REPO' (e.g. pytorch/pytorch)", err=True)
        sys.exit(1)

    click.echo(f"Fetching data for repository: {repository} (limit={limit})")
    
    # We set use_cache=False to force a fresh fetch from API and overwrite cache
    client = GitHubClient(use_cache=False)
    
    try:
        repo_info = client.fetch_repository_info(repository)
        click.echo(f"[OK] Repository info cached: {repo_info.owner}/{repo_info.name} ({repo_info.stars} stars)")
        
        issues = client.fetch_issues(repository, state="all", limit=limit)
        click.echo(f"[OK] {len(issues)} issues fetched and cached.")
        
        click.echo("\nAll data successfully cached to 'data/cache/'. Ready for offline replay mode!")
    except Exception as e:
        # Avoid printing unicode errors on Windows shell if possible
        try:
            click.echo(f"\n[Error] Failed fetching data: {e}", err=True)
        except Exception:
            click.echo("\n[Error] Failed fetching data due to print encoding error.", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
