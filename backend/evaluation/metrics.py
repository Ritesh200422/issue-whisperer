"""Metrics helper for evaluating duplicate detection results."""
from __future__ import annotations


def calculate_metrics(predictions: list[dict], ground_truths: list[dict]) -> dict:
    """Calculate duplicate detection F1, precision, recall, label accuracy, and false duplicate rate."""
    tp = 0  # True Positives: Predicted duplicate, is duplicate
    fp = 0  # False Positives: Predicted duplicate, is NOT duplicate
    fn = 0  # False Negatives: Predicted non-duplicate, is duplicate
    tn = 0  # True Negatives: Predicted non-duplicate, is NOT duplicate
    
    correct_labels = 0
    total = len(predictions)
    
    for pred, gt in zip(predictions, ground_truths):
        pred_dup = pred.get("is_duplicate", False)
        gt_dup = gt.get("expected_is_duplicate", False)
        
        # Duplicate detection counts
        if pred_dup and gt_dup:
            tp += 1
        elif pred_dup and not gt_dup:
            fp += 1
        elif not pred_dup and gt_dup:
            fn += 1
        else:
            tn += 1
            
        # Label accuracy counts
        if pred.get("label", "").lower() == gt.get("expected_label", "").lower():
            correct_labels += 1
            
    # Calculate scores
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # False Duplicate Rate: false duplicates / total duplicate predictions
    fdr = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    label_accuracy = correct_labels / total if total > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_duplicate_rate": fdr,
        "label_accuracy": label_accuracy,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn
    }
