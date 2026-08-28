"""Approval service simulating GitHub duplicate management actions."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ApprovalService:
    """Simulates GitHub API mutations (comments, label changes, state changes) safely."""

    def simulate_action(
        self,
        issue_number: int,
        action: str,  # "approve", "reject", "edit"
        suggested_label: str,
        duplicate_of: int | None = None,
        edited_reply: str | None = None
    ) -> dict:
        """Process and simulate issue triage resolution actions."""
        logger.info(
            "Received human approval resolution for issue #%d | Action: %s",
            issue_number,
            action
        )
        
        simulated_log = []
        
        if action == "approve":
            simulated_log.append(f"Adding label: '{suggested_label}' to issue #{issue_number}")
            if duplicate_of:
                simulated_log.append(f"Adding label: 'duplicate' to issue #{issue_number}")
                reply_body = edited_reply or f"This issue is a duplicate of #{duplicate_of}."
                simulated_log.append(f"Posting comment to issue #{issue_number}: '{reply_body}'")
                simulated_log.append(f"Closing issue #{issue_number} as duplicate.")
            else:
                reply_body = edited_reply or "Thank you for the report! We have labeled it appropriately."
                simulated_log.append(f"Posting comment to #{issue_number}: '{reply_body}'")
                
        elif action == "edit":
            simulated_log.append(f"Adding custom label: '{suggested_label}' to issue #{issue_number}")
            if duplicate_of:
                simulated_log.append(f"Adding label: 'duplicate' to issue #{issue_number}")
            reply_body = edited_reply or "Issue resolved with edited comment."
            simulated_log.append(f"Posting custom comment to issue #{issue_number}: '{reply_body}'")
            if duplicate_of:
                simulated_log.append(f"Closing issue #{issue_number} as duplicate.")
                
        elif action == "reject":
            simulated_log.append(f"Triage recommendation for issue #{issue_number} was rejected by human.")
            simulated_log.append("No actions performed on GitHub.")
            
        else:
            raise ValueError(f"Unknown resolution action type: {action}")
            
        logger.info("Simulation complete: %d actions simulated.", len(simulated_log))
        
        return {
            "issue_number": issue_number,
            "action": action,
            "success": True,
            "simulated_actions": simulated_log
        }
