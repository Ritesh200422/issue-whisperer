"""FAISS vector index manager for local issue search."""
from __future__ import annotations

import json
import logging
from pathlib import Path
import faiss
import numpy as np

from backend.models.issue import IssueModel
from backend.services.config_service import get_config

logger = logging.getLogger(__name__)


class EmbeddingIndex:
    """Manages a FAISS vector index and associated issue metadata."""

    def __init__(self, index_dir: str | None = None):
        config = get_config()
        self.index_dir = Path(index_dir or config.data.index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.index_dir / "issues.faiss"
        self.metadata_file = self.index_dir / "metadata.json"
        
        self.index: faiss.IndexFlatIP | None = None
        self.metadata: list[dict] = []

    def build(self, embeddings: np.ndarray, issues: list[IssueModel]) -> None:
        """Build a new FAISS index from scratch with the given embeddings."""
        if len(embeddings) == 0:
            logger.warning("Empty embeddings list provided to index build.")
            return

        dimension = embeddings.shape[1]
        
        # Normalize embeddings for cosine similarity using Inner Product index
        faiss.normalize_L2(embeddings)
        
        # IndexFlatIP matches Inner Product (equivalent to Cosine Similarity after L2 normalization)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        
        self.metadata = [issue.model_dump() for issue in issues]
        self.save()

    def save(self) -> None:
        """Serialize FAISS index and metadata to disk."""
        if self.index is None:
            logger.error("Cannot save: Index is not initialized.")
            return
            
        faiss.write_index(self.index, str(self.index_file))
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        logger.info("Saved FAISS index and metadata to %s", self.index_dir)

    def load(self) -> bool:
        """Load FAISS index and metadata from disk."""
        if not self.index_file.exists() or not self.metadata_file.exists():
            logger.warning("FAISS index files not found in %s", self.index_dir)
            return False
            
        try:
            self.index = faiss.read_index(str(self.index_file))
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            logger.info("Successfully loaded FAISS index with %d issues", len(self.metadata))
            return True
        except Exception as e:
            logger.error("Error loading FAISS index: %s", e)
            return False

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[tuple[IssueModel, float]]:
        """Search the FAISS index for top_k matches."""
        if self.index is None:
            if not self.load():
                logger.error("Index not loaded or available.")
                return []
                
        # Normalize the query embedding for cosine similarity
        query_normalized = query_embedding.copy()
        faiss.normalize_L2(query_normalized)
        
        # Search index
        scores, indices = self.index.search(query_normalized, top_k)
        
        results: list[tuple[IssueModel, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            issue_data = self.metadata[idx]
            results.append((IssueModel(**issue_data), float(score)))
            
        return results
