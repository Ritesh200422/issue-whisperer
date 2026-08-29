"""Core Triage Service coordinating retrieval, classification, and verification pipelines."""
from __future__ import annotations

import logging
from pathlib import Path
from backend.agents.triage_agent import TriageAgent
from backend.agents.verifier_agent import VerifierAgent
from backend.models.issue import IssueModel
from backend.models.triage import TriageModel
from backend.models.verification import VerificationModel
from backend.tools.retrieval import IssueRetrieval
from backend.services.config_service import get_config

logger = logging.getLogger(__name__)


class TriageService:
    """Manages the full issue analysis workflow from retrieval to independent verification."""

    def __init__(self):
        self.config = get_config()
        self.retrieval = IssueRetrieval()
        self.triage_agent = TriageAgent()
        self.verifier_agent = VerifierAgent()

    def analyze_issue(self, title: str, body: str | None = None) -> dict:
        """Run the complete pipeline: retrieve historical issues, triage, verify claims."""
        # 1. Create issue model
        new_issue = IssueModel(
            number=999,  # placeholder for new incoming issue
            title=title,
            body=body or "",
            labels=[]
        )
        
        # 2. Retrieve top-k candidates
        logger.info("Retrieving duplicate candidates for issue: %s", title)
        candidates = self.retrieval.retrieve_similar_issues(
            title=title,
            body=body,
            top_k=self.config.retrieval.top_k,
            similarity_threshold=self.config.retrieval.similarity_threshold
        )
        logger.info("Found %d candidates above similarity threshold.", len(candidates))

        # Read README context if available for the agent
        readme_context = ""
        readme_path = Path(self.config.github.cache_dir) / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_context = f.read()
            except Exception as e:
                logger.warning("Failed to load cached README.md: %s", e)

        # 3. Classify with Triage Agent
        logger.info("Running Triage Agent...")
        triage_decision = self.triage_agent.triage_issue(
            new_issue=new_issue,
            candidates=candidates,
            readme_context=readme_context
        )
        logger.info("Triage Agent suggested label: %s | Duplicate claim: %s", triage_decision.label, triage_decision.is_duplicate)

        # 4. Run Independent Verifier Agent if a duplicate was claimed
        verification_result = None
        
        if triage_decision.is_duplicate and triage_decision.duplicate_of is not None:
            # Find the target candidate issue
            target_candidate = None
            for c in candidates:
                if c["number"] == triage_decision.duplicate_of:
                    target_candidate = IssueModel(
                        number=c["number"],
                        title=c["title"],
                        body=c["body"] or "",
                        labels=c["labels"],
                        state=c["state"]
                    )
                    break
            
            if target_candidate:
                logger.info("Running Verifier Agent against candidate #%d...", target_candidate.number)
                verification_result = self.verifier_agent.verify_claim(
                    new_issue=new_issue,
                    candidate_issue=target_candidate,
                    triage_claim=triage_decision
                )
                logger.info("Verifier Agent status: %s", verification_result.status)
            else:
                # Candidate not found in retrieved list (should not happen, but safe fallback)
                logger.warning("Claimed duplicate target issue #%d not in retrieved candidates.", triage_decision.duplicate_of)
                verification_result = VerificationModel(
                    status="not_duplicate",
                    reason="Verification skipped: claimed duplicate target issue not found in retrieved results.",
                    evidence_quote=None
                )
        else:
            # No duplicate claimed
            verification_result = VerificationModel(
                status="not_duplicate",
                reason="Triage agent did not identify this issue as a duplicate.",
                evidence_quote=None
            )

        # Apply Case 2 & 3 failure handling overrides
        final_is_duplicate = triage_decision.is_duplicate
        final_duplicate_of = triage_decision.duplicate_of
        final_evidence = triage_decision.evidence_quote
        
        # Override to possibly_related or not_duplicate if verifier disagrees
        if verification_result.status == "not_duplicate":
            final_is_duplicate = False
            final_duplicate_of = None
            final_evidence = None
        elif verification_result.status == "possibly_related":
            # Map Case 2: triage says duplicate, verifier rejects/marks possibly related
            final_is_duplicate = False
            final_duplicate_of = triage_decision.duplicate_of
            final_evidence = None

        return {
            "label": triage_decision.label,
            "is_duplicate": final_is_duplicate,
            "duplicate_of": final_duplicate_of,
            "confidence": triage_decision.confidence,
            "evidence_quote": final_evidence,
            "draft_reply": triage_decision.draft_reply,
            "retrieved_candidates": candidates,
            "triage": triage_decision.model_dump(),
            "verification": verification_result.model_dump()
        }
