"""Unit tests for the independent Verifier Agent and programmatic evidence checks."""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import pytest
from agents.verifier_agent import VerifierAgent
from models.issue import IssueModel
from models.triage import TriageModel
from models.verification import VerificationModel


class MockLLMService:
    """Mock LLM to return preset JSON responses for verifier tests."""
    
    def __init__(self, response_content: str):
        self.response_content = response_content

    def chat_completion(self, system_prompt, user_prompt, json_mode=False, temperature=None):
        return self.response_content


def test_programmatic_evidence_validation_success():
    """Verify programmatic check passes when evidence exists in candidate text."""
    new_issue = IssueModel(number=101, title="New Issue", body="crashes on load")
    candidate_issue = IssueModel(number=42, title="Old Crash", body="Application crashes when uploading files.")
    triage_claim = TriageModel(
        label="bug",
        is_duplicate=True,
        duplicate_of=42,
        confidence=0.8,
        evidence_quote="crashes when uploading",
        draft_reply="dup"
    )
    
    # Mock output where verifier finds valid evidence quote
    mock_json = '{"status": "confirmed", "reason": "Both crash", "evidence_quote": "crashes when uploading"}'
    verifier = VerifierAgent(llm_service=MockLLMService(mock_json))
    
    result = verifier.verify_claim(new_issue, candidate_issue, triage_claim)
    assert result.status == "confirmed"
    assert result.evidence_quote == "crashes when uploading"


def test_programmatic_evidence_validation_failure():
    """Verify programmatic check rejects and overrides status when evidence is hallucinated/absent."""
    new_issue = IssueModel(number=101, title="New Issue", body="crashes on load")
    candidate_issue = IssueModel(number=42, title="Old Crash", body="Application crashes when uploading files.")
    triage_claim = TriageModel(
        label="bug",
        is_duplicate=True,
        duplicate_of=42,
        confidence=0.8,
        evidence_quote="non-existent text",
        draft_reply="dup"
    )
    
    # Verifier reports confirmed status but returns hallucinated evidence quote not in candidate_issue
    mock_json = '{"status": "confirmed", "reason": "Both crash", "evidence_quote": "absent string quote"}'
    verifier = VerifierAgent(llm_service=MockLLMService(mock_json))
    
    result = verifier.verify_claim(new_issue, candidate_issue, triage_claim)
    # The programmatic check must override the status to not_duplicate
    assert result.status == "not_duplicate"
    assert "Verification failed" in result.reason
    assert result.evidence_quote is None
