"""High-level issue retrieval service wrapper."""
from __future__ import annotations

import logging
from backend.models.issue import IssueModel
from backend.tools.embedding_index import EmbeddingIndex
from backend.tools.embedding_model import EmbeddingModel
from backend.services.config_service import get_config

logger = logging.getLogger(__name__)


class IssueRetrieval:
    """Combines embedding generation and vector database to retrieve similar issues."""

    def __init__(self, model: EmbeddingModel | None = None, index: EmbeddingIndex | None = None):
        self.config = get_config()
        self.model = model or EmbeddingModel()
        self.index = index or EmbeddingIndex()
        
        # Load index automatically if available
        self.index.load()

    def retrieve_similar_issues(
        self,
        title: str,
        body: str | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None
    ) -> list[dict]:
        """Search for top_k issues similar to the new issue title and body.

        Returns a list of dicts with issue details and search scores.
        """
        top_k = top_k or self.config.retrieval.top_k
        similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.config.retrieval.similarity_threshold
        )
        
        # Combine title and body to form the query text
        query_text = f"Title: {title}\nBody: {body or ''}"
        
        # Embed query text
        query_embedding = self.model.encode(query_text)
        
        # Search the FAISS index
        raw_results = self.index.search(query_embedding, top_k=top_k)
        
        retrieved: list[dict] = []
        for issue, score in raw_results:
            # Check threshold
            if score < similarity_threshold:
                logger.debug("Skipping candidate #%d due to low similarity: %.4f", issue.number, score)
                continue
                
            retrieved.append({
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "labels": issue.labels,
                "state": issue.state,
                "similarity_score": score,
                "html_url": issue.html_url,
                "user_login": issue.user_login
            })
            
        return retrieved
