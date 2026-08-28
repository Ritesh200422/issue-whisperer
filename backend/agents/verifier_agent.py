"""Verifier Agent implementing independent claim evaluation and substring evidence validation."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from agents.prompts import VERIFIER_SYSTEM_PROMPT, VERIFIER_USER_TEMPLATE
from models.issue import IssueModel
from models.triage import TriageModel
from models.verification import VerificationModel
from services.config_service import get_config
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class VerifierAgent:
    """Agent for verifying duplicate claims with strict programmatic evidence checking."""

    def __init__(self, llm_service: LLMService | None = None):
        self.config = get_config()
        self.llm = llm_service or LLMService()
        
        # Directory for trajectories
        self.trajectory_dir = Path(self.config.data.cache_dir).parent.parent / "trajectories" / "verifier"
        self.trajectory_dir.mkdir(parents=True, exist_ok=True)

    def verify_claim(
        self,
        new_issue: IssueModel,
        candidate_issue: IssueModel,
        triage_claim: TriageModel
    ) -> VerificationModel:
        """Independently evaluate duplicate claims and verify physical text evidence."""
        user_prompt = VERIFIER_USER_TEMPLATE.format(
            new_title=new_issue.title,
            new_body=new_issue.body or "",
            candidate_number=candidate_issue.number,
            candidate_title=candidate_issue.title,
            candidate_body=candidate_issue.body or "",
            triage_draft_reply=triage_claim.draft_reply,
            triage_evidence=triage_claim.evidence_quote or ""
        )

        retries = 0
        raw_response = ""
        error_message = None
        validated = None

        # 1. Run LLM check
        try:
            raw_response = self.llm.chat_completion(
                system_prompt=VERIFIER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                json_mode=True
            )
            validated = VerificationModel(**json.loads(raw_response))
        except Exception as e:
            retries += 1
            error_message = str(e)
            logger.warning("Verifier output failed validation. Retrying once... Error: %s", e)
            
            corrective_user_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response failed validation:\n{raw_response}\n\n"
                f"Error: {e}\n"
                f"Please output ONLY valid JSON matching the schema correctly."
            )
            try:
                raw_response = self.llm.chat_completion(
                    system_prompt=VERIFIER_SYSTEM_PROMPT,
                    user_prompt=corrective_user_prompt,
                    json_mode=True
                )
                validated = VerificationModel(**json.loads(raw_response))
            except Exception as final_err:
                logger.error("Verifier Agent corrective retry failed: %s", final_err)
                validated = VerificationModel(
                    status="not_duplicate",
                    reason=f"Verifier failed to process the claim. Error: {final_err}",
                    evidence_quote=None
                )

        # 2. Programmatic Evidence Validation
        # Check if the claimed evidence quote actually exists inside the candidate issue text
        if validated.status == "confirmed" and validated.evidence_quote:
            evidence_str = validated.evidence_quote.strip().lower()
            candidate_text = f"{candidate_issue.title}\n{candidate_issue.body or ''}".lower()
            
            # Simple exact substring check
            if evidence_str not in candidate_text:
                logger.warning(
                    "Programmatic verification failed: evidence quote '%s' not found in candidate #%d text.",
                    validated.evidence_quote,
                    candidate_issue.number
                )
                # Fail verification if evidence cannot be programmatically validated
                validated = VerificationModel(
                    status="not_duplicate",
                    reason=f"Verification failed: reported evidence quote '{validated.evidence_quote}' does not exist in the candidate issue text.",
                    evidence_quote=None
                )

        # 3. Log trajectory
        self._log_trajectory(
            new_issue=new_issue,
            candidate_issue=candidate_issue,
            triage_claim=triage_claim,
            raw_response=raw_response,
            validated=validated,
            retries=retries,
            error_message=error_message
        )

        return validated

    def _log_trajectory(
        self,
        new_issue: IssueModel,
        candidate_issue: IssueModel,
        triage_claim: TriageModel,
        raw_response: str,
        validated: VerificationModel,
        retries: int,
        error_message: str | None
    ) -> None:
        """Write verifier execution log trajectory."""
        if not self.config.trajectories.enabled:
            return
            
        timestamp = datetime.utcnow().isoformat()
        trajectory_data = {
            "timestamp": timestamp,
            "agent": "VerifierAgent",
            "system_prompt_version": "v1.0",
            "model": self.config.llm.model,
            "provider": self.config.llm.provider,
            "input": {
                "new_issue_number": new_issue.number,
                "candidate_issue_number": candidate_issue.number,
                "triage_is_duplicate": triage_claim.is_duplicate,
                "triage_evidence": triage_claim.evidence_quote
            },
            "retries": retries,
            "error_msg": error_message,
            "raw_response": raw_response,
            "final_verification": validated.model_dump()
        }
        
        file_path = self.trajectory_dir / f"verifier_{new_issue.number}_vs_{candidate_issue.number}_{int(datetime.utcnow().timestamp())}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            logger.info("Saved verifier trajectory log to %s", file_path)
        except Exception as e:
            logger.error("Failed writing verifier trajectory log: %s", e)
