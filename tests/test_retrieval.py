"""Unit tests for the embedding retrieval system."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import pytest
from tools.embedding_index import EmbeddingIndex
from tools.embedding_model import EmbeddingModel
from tools.retrieval import IssueRetrieval


def test_embedding_model_shape():
    """Verify embedding dimension matches model spec (all-MiniLM-L6-v2 is 384)."""
    model = EmbeddingModel(device="cpu")
    emb = model.encode("Test query")
    assert emb.shape == (1, 384)
    assert model.dimension == 384


def test_retrieval_service_flow():
    """Verify that retrieval runs end-to-end and returns expected structure."""
    # Ensure index is built and loaded
    retrieval = IssueRetrieval(
        model=EmbeddingModel(device="cpu"),
        index=EmbeddingIndex()
    )
    
    # Run retrieval
    results = retrieval.retrieve_similar_issues(
        title="bug report showing duplicate errors",
        body="crashes when uploading large files",
        top_k=2,
        similarity_threshold=0.0  # Let everything through for the test
    )
    
    assert isinstance(results, list)
    assert len(results) <= 2
    for item in results:
        assert "number" in item
        assert "title" in item
        assert "body" in item
        assert "similarity_score" in item
        assert isinstance(item["similarity_score"], float)
