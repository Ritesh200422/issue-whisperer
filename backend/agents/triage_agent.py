"""Triage Agent implementing structured duplicate detection reasoning."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from agents.prompts import TRIAGE_SYSTEM_PROMPT, TRIAGE_USER_TEMPLATE
from models.issue import IssueModel
from models.triage import TriageModel
from services.config_service import get_config
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class TriageAgent:
    """Agent for classifying issues and finding potential duplicate candidates."""

    def __init__(self, llm_service: LLMService | None = None):
        self.config = get_config()
        self.llm = llm_service or LLMService()
        
        # Output directory for execution trajectories
        self.trajectory_dir = Path(self.config.data.cache_dir).parent.parent / "trajectories" / "triage"
        self.trajectory_dir.mkdir(parents=True, exist_ok=True)

    def triage_issue(
        self,
        new_issue: IssueModel,
        candidates: list[dict],
        readme_context: str = ""
    ) -> TriageModel:
        """Triage a new issue against retrieved duplicate candidates."""
        # 1. Format candidates list for the prompt
        candidates_formatted = ""
        if not candidates:
            candidates_formatted = "No similar historical issues were found."
        else:
            for idx, c in enumerate(candidates):
                candidates_formatted += (
                    f"--- Candidate {idx + 1} ---\n"
                    f"Number: #{c['number']}\n"
                    f"Title: {c['title']}\n"
                    f"Body: {c['body'] or ''}\n"
                    f"Labels: {', '.join(c['labels'])}\n"
                    f"State: {c['state']}\n"
                    f"Similarity Score: {c['similarity_score']:.4f}\n\n"
                )

        user_prompt = TRIAGE_USER_TEMPLATE.format(
            title=new_issue.title,
            body=new_issue.body or "",
            readme_context=readme_context or "No repository documentation provided.",
            candidates=candidates_formatted
        )

        retries = 0
        raw_response = ""
        error_message = None

        # 2. Query LLM with retry loop for JSON/schema correction
        try:
            raw_response = self.llm.chat_completion(
                system_prompt=TRIAGE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                json_mode=True
            )
            validated = TriageModel(**json.loads(raw_response))
        except Exception as e:
            retries += 1
            error_message = str(e)
            logger.warning("Triage output failed validation. Retrying once... Error: %s", e)
            
            # Corrective prompt
            corrective_user_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response failed validation:\n{raw_response}\n\n"
                f"Error: {e}\n"
                f"Please output ONLY valid JSON matching the schema correctly."
            )
            try:
                raw_response = self.llm.chat_completion(
                    system_prompt=TRIAGE_SYSTEM_PROMPT,
                    user_prompt=corrective_user_prompt,
                    json_mode=True
                )
                validated = TriageModel(**json.loads(raw_response))
            except Exception as final_err:
                logger.error("Triage Agent corrective retry failed: %s", final_err)
                # Fallback model to handle complete failure gracefully
                validated = TriageModel(
                    label="bug",
                    is_duplicate=False,
                    duplicate_of=None,
                    confidence=0.0,
                    evidence_quote=None,
                    draft_reply=f"System failed to analyze this issue. Error: {final_err}"
                )

        # 3. Trajectory Logging
        self._log_trajectory(
            new_issue=new_issue,
            candidates=candidates,
            readme_context=readme_context,
            raw_response=raw_response,
            validated=validated,
            retries=retries,
            error_message=error_message
        )

        return validated

    def _log_trajectory(
        self,
        new_issue: IssueModel,
        candidates: list[dict],
        readme_context: str,
        raw_response: str,
        validated: TriageModel,
        retries: int,
        error_message: str | None
    ) -> None:
        """Write execution logs as trajectories for hackathon tracking."""
        if not self.config.trajectories.enabled:
            return
            
        timestamp = datetime.utcnow().isoformat()
        trajectory_data = {
            "timestamp": timestamp,
            "agent": "TriageAgent",
            "system_prompt_version": "v1.0",
            "model": self.config.llm.model,
            "provider": self.config.llm.provider,
            "input": {
                "title": new_issue.title,
                "body": new_issue.body,
                "readme_length": len(readme_context)
            },
            "retrieved_candidates": [
                {"number": c["number"], "similarity": c["similarity_score"]} for c in candidates
            ],
            "retries": retries,
            "error_msg": error_message,
            "raw_response": raw_response,
            "final_decision": validated.model_dump()
        }
        
        file_path = self.trajectory_dir / f"triage_{new_issue.number}_{int(datetime.utcnow().timestamp())}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            logger.info("Saved triage trajectory log to %s", file_path)
        except Exception as e:
            logger.error("Failed writing triage trajectory log: %s", e)
