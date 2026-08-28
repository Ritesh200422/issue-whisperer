"""Unit tests verifying Pydantic schema validation constraints."""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import pytest
from pydantic import ValidationError
from models.triage import TriageModel


def test_valid_triage_duplicate():
    """Verify correct Pydantic validation for a duplicate claim."""
    data = {
        "label": "bug",
        "is_duplicate": True,
        "duplicate_of": 12,
        "confidence": 0.85,
        "evidence_quote": "crashes on startup",
        "draft_reply": "This is a duplicate."
    }
    model = TriageModel(**data)
    assert model.is_duplicate is True
    assert model.duplicate_of == 12
    assert model.confidence == 0.85


def test_valid_triage_non_duplicate():
    """Verify correct Pydantic validation for a non-duplicate claim."""
    data = {
        "label": "feature",
        "is_duplicate": False,
        "duplicate_of": None,
        "confidence": 0.9,
        "evidence_quote": None,
        "draft_reply": "Thanks for the suggestion!"
    }
    model = TriageModel(**data)
    assert model.is_duplicate is False
    assert model.duplicate_of is None
    assert model.evidence_quote is None


def test_invalid_confidence():
    """Verify confidence score boundaries [0.0, 1.0] are enforced."""
    base_data = {
        "label": "bug",
        "is_duplicate": False,
        "duplicate_of": None,
        "evidence_quote": None,
        "draft_reply": "Response..."
    }
    
    with pytest.raises(ValidationError):
        TriageModel(confidence=1.1, **base_data)
        
    with pytest.raises(ValidationError):
        TriageModel(confidence=-0.1, **base_data)


def test_invalid_duplicate_logic():
    """Verify duplicate constraints (if duplicate target exists, is_duplicate must be True)."""
    # 1. is_duplicate = True but duplicate_of = None should raise ValidationError
    with pytest.raises(ValidationError):
        TriageModel(
            label="bug",
            is_duplicate=True,
            duplicate_of=None,
            confidence=0.8,
            evidence_quote="some evidence",
            draft_reply="..."
        )
        
    # 2. is_duplicate = False but duplicate_of is provided should raise ValidationError
    with pytest.raises(ValidationError):
        TriageModel(
            label="bug",
            is_duplicate=False,
            duplicate_of=42,
            confidence=0.8,
            evidence_quote=None,
            draft_reply="..."
        )
