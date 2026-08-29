#!/usr/bin/env python
"""Baseline script that performs a single LLM call without retrieval context."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Add repo root to path so `backend.*` imports work when run as a standalone script
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

import click
from dotenv import load_dotenv

from backend.agents.prompts import BASELINE_SYSTEM_PROMPT, BASELINE_USER_TEMPLATE
from backend.models.triage import TriageModel
from backend.services.llm_service import LLMService
from backend.logging_config import setup_logging

load_dotenv()
setup_logging("INFO")


def run_baseline_model(title: str, body: str) -> dict:
    """Evaluate an issue using the baseline LLM call without any database context."""
    llm = LLMService()
    
    user_prompt = BASELINE_USER_TEMPLATE.format(title=title, body=body)
    
    # Run the model with JSON Mode enabled
    raw_response = llm.chat_completion(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        json_mode=True
    )
    
    # Parse and validate with Pydantic
    try:
        data = json.loads(raw_response)
        validated = TriageModel(**data)
        return validated.model_dump()
    except Exception as e:
        # Corrective retry logic for malformed JSON
        logger = logging.getLogger(__name__)
        logger.warning("Baseline output failed verification, retrying: %s", e)
        
        corrective_user_prompt = (
            f"{user_prompt}\n\n"
            f"Your previous response failed validation: {raw_response}\n"
            f"Error: {e}\n"
            f"Please output ONLY valid JSON matching the schema correctly."
        )
        
        retry_raw = llm.chat_completion(
            system_prompt=BASELINE_SYSTEM_PROMPT,
            user_prompt=corrective_user_prompt,
            json_mode=True
        )
        data = json.loads(retry_raw)
        validated = TriageModel(**data)
        return validated.model_dump()


@click.command()
@click.option("--title", required=True, help="Title of the new issue.")
@click.option("--body", default="", help="Body of the new issue.")
def main(title: str, body: str) -> None:
    """Run duplicate detection baseline against local LLM model."""
    click.echo(f"Running baseline detection for: '{title}'")
    try:
        result = run_baseline_model(title, body)
        click.echo("\n--- Baseline Structured Output ---")
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error running baseline: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
