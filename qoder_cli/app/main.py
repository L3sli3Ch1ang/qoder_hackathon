"""SkillBridge — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipeline on startup."""
    logger.info("Starting SkillBridge — initializing pipeline...")
    from app.pipeline.orchestrator import PipelineOrchestrator
    PipelineOrchestrator.get_instance()
    logger.info("SkillBridge ready.")
    yield


app = FastAPI(title="SkillBridge", version="0.1.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(api_router)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@lru_cache(maxsize=1)
def _convergence() -> list[dict]:
    """Precomputed pairwise sector skill overlap (cached for the process)."""
    from app.pipeline.sector_convergence import SectorConvergence

    return SectorConvergence().run()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main application page."""
    from app.data import get_whatif_skills

    return templates.TemplateResponse(
        request,
        "index.html",
        {"convergence": _convergence(), "whatif_skills": get_whatif_skills()},
    )
