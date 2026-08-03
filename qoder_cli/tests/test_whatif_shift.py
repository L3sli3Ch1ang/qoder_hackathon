"""Regression tests: What-If skill additions must actually shift match results.

Guards the two bugs that made the What-If explorer appear to do nothing:
  1. Added skills that were not real SWDA taxonomy skills were never
     extracted, so they had zero effect (fixed by sourcing the explorer's
     checkboxes from the live taxonomy via ``get_whatif_skills``).
  2. When the JD mentioned a seeded job, ``_resolve_required_levels`` returned
     only that job's requirements and silently dropped every other skill —
     including the What-If addition — out of the proficiency fit.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.data import get_all_skills, get_whatif_skills
from app.main import app
from app.pipeline.orchestrator import PipelineOrchestrator

RANKED_JD = (
    "Account Operations Analyst in finance. Strong Business Planning, Data Governance, "
    "Regulatory Compliance, Quality Assurance and Financial Statements Review required. "
    "Customer account processing, collateral management and ethical culture experience preferred."
)

# A real taxonomy skill that is NOT mentioned in RANKED_JD.
ADDED_SKILL = "Stakeholder Management"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient with an isolated Qdrant store and offline narratives."""
    qdrant_dir = tmp_path_factory.mktemp("qdrant_whatif")
    orig_qdrant = settings.QDRANT_PATH
    orig_key = settings.DASHSCOPE_API_KEY
    settings.QDRANT_PATH = str(qdrant_dir)
    settings.DASHSCOPE_API_KEY = ""  # force offline fallback narrative
    PipelineOrchestrator._instance = None  # rebuild with test settings
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        PipelineOrchestrator._instance = None
        settings.QDRANT_PATH = orig_qdrant
        settings.DASHSCOPE_API_KEY = orig_key


def test_whatif_skills_are_all_real_taxonomy_skills():
    """Every curated What-If checkbox skill exists in the live taxonomy.

    Guards bug #1: a checkbox skill absent from the taxonomy is never
    extracted and therefore has no effect on match scores.
    """
    whatif = get_whatif_skills()
    assert whatif, "What-If skill list must not be empty"
    known = get_all_skills()
    for skill in whatif:
        assert skill in known, f"What-If skill {skill!r} is not a real taxonomy skill"


def test_added_skill_is_a_real_taxonomy_skill():
    """The What-If addition used in these tests exists in the live taxonomy."""
    assert ADDED_SKILL in get_all_skills()


def test_whatif_addition_appears_in_analysis(client):
    """An added skill is extracted and lands in every candidate's matched/gap."""
    resp = client.post("/api/match", json={
        "jd_text": RANKED_JD, "mode": "ranked", "added_skills": [ADDED_SKILL],
    })
    results = resp.json()["results"]
    assert results
    for r in results:
        assert ADDED_SKILL in r["matched"] + r["gap"], (
            f"{r['candidate_id']}: added skill {ADDED_SKILL!r} was not evaluated"
        )


def test_whatif_addition_shifts_proficiency_fit(client):
    """Regression (bug #2): adding a skill to a JD that names a seeded job must
    still change the proficiency fit (previously the addition was dropped)."""
    base = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "ranked"}).json()["results"]
    whatif = client.post("/api/match", json={
        "jd_text": RANKED_JD, "mode": "ranked", "added_skills": [ADDED_SKILL],
    }).json()["results"]
    base_fits = {r["candidate_id"]: r["proficiency_fit"] for r in base}
    assert any(
        r["proficiency_fit"] != base_fits.get(r["candidate_id"]) for r in whatif
    ), "What-If addition did not shift any candidate's proficiency fit"


def test_resolve_required_levels_covers_every_skill():
    """Every extracted skill gets a required level, even when a seeded job
    title is present in the JD (the addition must never be dropped)."""
    orch = object.__new__(PipelineOrchestrator)  # skip __init__ (no model load)
    jd_skills = ["Data Governance", ADDED_SKILL]
    levels = orch._resolve_required_levels(RANKED_JD, jd_skills)
    assert set(levels.keys()) == set(jd_skills)
    assert all(isinstance(v, int) and 1 <= v <= 6 for v in levels.values())


def test_match_seeded_job_ignores_generic_titles():
    """A distinct role that merely contains a generic seeded title (e.g.
    'Engineer') must not be hijacked by that generic job's requirements."""
    match = PipelineOrchestrator._match_seeded_job
    assert match("Senior Data Engineer: build petabyte-scale data pipelines.") is None
    assert match("IoT Data Engineer for an industrial platform.") is None


def test_match_seeded_job_finds_verbatim_title():
    """A seeded job title mentioned verbatim is still matched (intended path)."""
    job = PipelineOrchestrator._match_seeded_job(
        "We are hiring an Account Operations Analyst for our private bank."
    )
    assert job is not None
    assert job["title"] == "Account Operations Analyst"
