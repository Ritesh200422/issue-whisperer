"""Issue Whisperer — FastAPI backend entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.logging_config import setup_logging
from backend.services.config_service import get_config
from backend.services.triage_service import TriageService
from backend.services.approval_service import ApprovalService

logger = logging.getLogger(__name__)


# ── API Request schemas ───────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    title: str
    body: str | None = ""


class ApproveRequest(BaseModel):
    issue_number: int
    action: str  # "approve", "reject", "edit"
    suggested_label: str
    duplicate_of: int | None = None
    edited_reply: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    cfg = get_config()
    logger.info("Issue Whisperer starting — version %s", cfg.app.version)
    yield
    logger.info("Issue Whisperer shutting down")


def create_app() -> FastAPI:
    cfg = get_config()
    setup_logging(cfg.app.log_level)

    app = FastAPI(
        title=cfg.app.name,
        version=cfg.app.version,
        description="AI agent for detecting duplicate GitHub issues.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Instantiate services
    triage_service = TriageService()
    approval_service = ApprovalService()

    # ── Routes ────────────────────────────────────────────────────────────────

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        """Return backend health status."""
        return {
            "status": "ok",
            "app": cfg.app.name,
            "version": cfg.app.version,
        }

    @app.post("/analyze", tags=["agent"])
    async def analyze(payload: AnalyzeRequest) -> dict:
        """Run the duplicate detection agent flow on a new issue."""
        try:
            result = triage_service.analyze_issue(
                title=payload.title,
                body=payload.body
            )
            return result
        except Exception as e:
            logger.error("Analysis route failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/approve", tags=["agent"])
    async def approve(payload: ApproveRequest) -> dict:
        """Approve or resolve the triage recommendation."""
        try:
            result = approval_service.simulate_action(
                issue_number=payload.issue_number,
                action=payload.action,
                suggested_label=payload.suggested_label,
                duplicate_of=payload.duplicate_of,
                edited_reply=payload.edited_reply
            )
            return result
        except Exception as e:
            logger.error("Approve route failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    cfg = get_config()
    uvicorn.run(
        "main:app",
        host=cfg.server.host,
        port=cfg.server.port,
        reload=True,
        log_level=cfg.app.log_level.lower(),
    )
