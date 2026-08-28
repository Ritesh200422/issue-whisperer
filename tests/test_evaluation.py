"""Unit tests verifying duplicate detection evaluation metrics."""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import pytest
from evaluation.metrics import calculate_metrics


def test_metrics_calculation_standard():
    """Verify metrics match expected precision/recall mathematical values."""
    ground_truths = [
        {"expected_is_duplicate": True, "expected_label": "bug"},
        {"expected_is_duplicate": True, "expected_label": "bug"},
        {"expected_is_duplicate": False, "expected_label": "feature"},
        {"expected_is_duplicate": False, "expected_label": "feature"}
    ]
    
    predictions = [
        {"is_duplicate": True, "label": "bug"},       # TP
        {"is_duplicate": False, "label": "bug"},      # FN
        {"is_duplicate": True, "label": "feature"},   # FP
        {"is_duplicate": False, "label": "bug"}       # TN (labels: pred bug, expected feature -> mismatch)
    ]
    
    results = calculate_metrics(predictions, ground_truths)
    
    # tp=1, fp=1, fn=1, tn=1
    # precision = 1 / 2 = 0.5
    # recall = 1 / 2 = 0.5
    # f1 = 0.5
    # label_accuracy: gt = [bug, bug, feature, feature], pred = [bug, bug, feature, bug] -> 3/4 match -> 0.75
    assert results["precision"] == 0.5
    assert results["recall"] == 0.5
    assert results["f1"] == 0.5
    assert results["false_duplicate_rate"] == 0.5
    assert results["label_accuracy"] == 0.75
