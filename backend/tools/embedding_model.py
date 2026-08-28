"""Embedding model wrapper using sentence-transformers."""
from __future__ import annotations

import logging
import numpy as np
from sentence_transformers import SentenceTransformer

from services.config_service import get_config

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for local SentenceTransformer model."""

    def __init__(self, model_name: str | None = None, device: str | None = None):
        config = get_config()
        self.model_name = model_name or config.embeddings.model
        self.device = device or config.embeddings.device
        
        logger.info("Initializing embedding model: %s on device: %s", self.model_name, self.device)
        self.model = SentenceTransformer(self.model_name, device=self.device)

    def encode(self, texts: list[str] | str, batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts or a single text."""
        if isinstance(texts, str):
            texts = [texts]
        
        # sentence-transformers returns a numpy array
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return np.array(embeddings, dtype=np.float32)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension size."""
        return self.model.get_sentence_embedding_dimension()
