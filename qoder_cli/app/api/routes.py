"""API routes for SkillBridge matching pipeline."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.api.schemas import CandidateProfile, MatchRequest, MatchResponse
from app.data import get_candidate_by_id
from app.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.post("/match")
async def match(request: Request, body: MatchRequest):
    """Run the matching pipeline and return results.

    Returns HTML partial for HTMX requests, JSON otherwise.
    """
    try:
        orchestrator = PipelineOrchestrator.get_instance()
        results = await orchestrator.match(
            jd_text=body.jd_text,
            mode=body.mode,
            added_skills=body.added_skills or None,
            removed_skills=body.removed_skills or None,
        )

        # Check if this is an HTMX request
        is_htmx = request.headers.get("HX-Request") == "true"

        if is_htmx:
            return templates.TemplateResponse(
                request,
                "partials/results.html",
                {
                    "results": results,
                    "mode": body.mode,
                    "perspective": body.perspective,
                    "total": len(results),
                },
            )

        # JSON response
        response = MatchResponse(
            results=results,
            mode=body.mode,
            total=len(results),
        )
        return response

    except Exception as e:
        logger.exception("Pipeline error: %s", e)
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            return templates.TemplateResponse(
                request,
                "partials/results.html",
                {
                    "results": [],
                    "mode": body.mode,
                    "perspective": body.perspective,
                    "total": 0,
                    "error": str(e),
                },
                status_code=200,
            )
        return {"error": str(e), "results": [], "total": 0}


@router.get("/candidate/{candidate_id}", response_model=CandidateProfile)
async def candidate_profile(candidate_id: str):
    """Return the full profile (CV detail) for a single candidate.

    Powers the recruiter-facing "View full profile" modal so the narrative's
    claims can be checked against the candidate's actual skills, proficiency
    levels, certifications and summary.
    """
    candidate = get_candidate_by_id(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return CandidateProfile(
        id=candidate["id"],
        name=candidate.get("name", ""),
        sector=candidate.get("sector", ""),
        title=candidate.get("title", ""),
        years_experience=candidate.get("years_experience", 0),
        skills=candidate.get("skills", []),
        skill_levels=candidate.get("skill_levels", {}),
        certifications=candidate.get("certifications", []),
        summary=candidate.get("summary", ""),
    )
