#!/usr/bin/env python
"""Replay mode — runs the full agent pipeline against locally cached data.

This allows the application to run fully offline without live GitHub API access.
Useful for demos, evaluation, and reproducibility without hitting rate limits.

Usage:
    python scripts/replay.py --title "Bug title" --body "Bug description"
    python scripts/replay.py --title "Bug title" --body "Bug description" --no-verify
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

# Resolve project root and add backend to path
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from logging_config import setup_logging
from services.config_service import get_config
from services.triage_service import TriageService
from tools.embedding_index import EmbeddingIndex
from tools.retrieval import IssueRetrieval

load_dotenv()
setup_logging("INFO")
logger = logging.getLogger(__name__)


def check_replay_data_available() -> bool:
    """Check whether the local cached data and FAISS index exist."""
    cfg = get_config()
    cache_dir = project_root / cfg.github.cache_dir
    index_dir = project_root / cfg.data.index_dir

    issues_file = cache_dir / "issues.json"
    faiss_index = index_dir / "issues.faiss"
    metadata_file = index_dir / "metadata.json"

    missing = []
    if not issues_file.exists():
        missing.append(str(issues_file))
    if not faiss_index.exists():
        missing.append(str(faiss_index))
    if not metadata_file.exists():
        missing.append(str(metadata_file))

    if missing:
        logger.error("Replay mode requires cached data. Missing files:\n  %s", "\n  ".join(missing))
        logger.error(
            "Run these commands first:\n"
            "  python scripts/fetch_data.py OWNER/REPO\n"
            "  python scripts/build_index.py"
        )
        return False

    return True


@click.command()
@click.option("--title", required=True, help="Title of the issue to analyze.")
@click.option("--body", default="", help="Body text of the issue to analyze.")
@click.option(
    "--no-verify",
    is_flag=True,
    default=False,
    help="Skip the Verifier Agent (ablation mode).",
)
@click.option("--top-k", default=3, show_default=True, help="Number of similar issues to retrieve.")
def main(title: str, body: str, no_verify: bool, top_k: int) -> None:
    """Run the Issue Whisperer pipeline in offline replay mode.

    Uses locally cached GitHub data and FAISS index — no live API calls required.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  ISSUE WHISPERER — REPLAY MODE (Offline)")
    click.echo("=" * 60)

    if not check_replay_data_available():
        sys.exit(1)

    click.echo(f"\nAnalyzing issue: '{title}'")
    if no_verify:
        click.echo("[Ablation] Verifier Agent is DISABLED for this run.")

    try:
        service = TriageService()
        result = service.analyze_issue(title=title, body=body)
    except Exception as e:
        click.echo(f"\nError during analysis: {e}", err=True)
        sys.exit(1)

    click.echo("\n--- Retrieved Candidates ---")
    candidates = result.get("retrieved_candidates", [])
    if candidates:
        for c in candidates:
            click.echo(f"  #{c['number']} [{c['similarity_score']:.3f}] {c['title']}")
    else:
        click.echo("  (No similar issues found above threshold)")

    triage = result.get("triage", {})
    click.echo("\n--- Triage Agent Decision ---")
    click.echo(f"  Label:       {triage.get('label')}")
    click.echo(f"  Duplicate:   {triage.get('is_duplicate')} (of #{triage.get('duplicate_of')})" if triage.get("is_duplicate") else f"  Duplicate:   {triage.get('is_duplicate')}")
    click.echo(f"  Confidence:  {triage.get('confidence', 0):.0%}")
    click.echo(f"  Evidence:    {triage.get('evidence_quote') or 'N/A'}")

    if not no_verify:
        verif = result.get("verification", {})
        click.echo("\n--- Verifier Agent Decision ---")
        click.echo(f"  Status:  {verif.get('status')}")
        click.echo(f"  Reason:  {verif.get('reason')}")
        click.echo(f"  Evidence quote verified: {verif.get('evidence_quote') or 'N/A'}")

    click.echo("\n--- Final Consolidated Decision ---")
    click.echo(json.dumps({
        "label": result.get("label"),
        "is_duplicate": result.get("is_duplicate"),
        "duplicate_of": result.get("duplicate_of"),
        "confidence": result.get("confidence"),
        "evidence_quote": result.get("evidence_quote"),
        "draft_reply": result.get("draft_reply"),
    }, indent=2))

    click.echo("\n[NOTE] No GitHub write actions were performed. This is a simulation.")
    click.echo("=" * 60 + "\n")


if __name__ == "__main__":
    main()
