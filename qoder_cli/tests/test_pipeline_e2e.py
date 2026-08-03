"""End-to-end pipeline tests via the FastAPI TestClient.

Hermetic by design: Qdrant uses an isolated temp store and the DashScope
API key is blanked so narrative generation uses the offline template
fallback (no network). The orchestrator singleton is reset so it rebuilds
with these test settings.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.data import get_candidates
from app.main import app
from app.pipeline.orchestrator import PipelineOrchestrator

RANKED_JD = (
    "Account Operations Analyst in finance. Strong Business Planning, Data Governance, "
    "Regulatory Compliance, Quality Assurance and Financial Statements Review required. "
    "Customer account processing, collateral management and ethical culture experience preferred."
)

RESULT_FIELDS = {
    "candidate_id", "name", "title", "sector", "years_experience",
    "score", "narrative", "matched", "gap", "bridge", "courses", "is_surprise",
}


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient with an isolated Qdrant store and offline narratives."""
    qdrant_dir = tmp_path_factory.mktemp("qdrant_e2e")
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


def test_ranked_returns_ten_enriched_results(client):
    """Ranked mode returns 10 fully enriched results."""
    resp = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "ranked"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "ranked"
    assert body["total"] == 10
    assert len(body["results"]) == 10
    for r in body["results"]:
        assert RESULT_FIELDS.issubset(r.keys())
        assert isinstance(r["score"], int) and 40 <= r["score"] <= 98
        assert isinstance(r["narrative"], str) and r["narrative"]
        assert isinstance(r["matched"], list)
        assert isinstance(r["gap"], list)
        assert isinstance(r["courses"], list)
        assert r["is_surprise"] is False
        # Proficiency-aware fields (additive)
        if r.get("proficiency_fit") is not None:
            assert 0.0 <= r["proficiency_fit"] <= 1.0
        for detail in r.get("matched_detail", []):
            assert "skill" in detail
            assert "met" in detail


def test_ranked_results_have_courses_for_gaps(client):
    """Each gap skill maps to exactly one course recommendation."""
    resp = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "ranked"})
    results = resp.json()["results"]
    for r in results:
        assert len(r["courses"]) == len(r["gap"])
        for course in r["courses"]:
            assert {"skill", "course_name", "provider", "url"}.issubset(course.keys())


def test_surprise_flags_all_results(client):
    """Surprise mode flags every returned result."""
    resp = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "surprise"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "surprise"
    assert body["total"] == 10
    assert len(body["results"]) == 10
    for r in body["results"]:
        assert r["is_surprise"] is True


def test_surprise_skills_align_to_correct_candidate(client):
    """Regression: surprise re-ordering keeps skills tied to their candidate.

    Guards the fixed orchestrator bug where ``skills_list`` (original order)
    was zipped against the surprise-re-ordered candidates, attaching another
    candidate's matched/gap skills. Invariants that must hold for every result:
      * matched skills are a subset of the candidate's actual skills
      * gap skills are disjoint from the candidate's actual skills
    """
    cand_skills = {
        c["id"]: {s.lower() for s in c.get("skills", [])}
        for c in get_candidates()
    }
    resp = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "surprise"})
    results = resp.json()["results"]
    assert results, "expected surprise results"
    for r in results:
        actual = cand_skills[r["candidate_id"]]
        matched_lower = {s.lower() for s in r["matched"]}
        gap_lower = {s.lower() for s in r["gap"]}
        assert matched_lower.issubset(actual), (
            f"{r['candidate_id']}: matched {matched_lower - actual} not in profile"
        )
        assert gap_lower.isdisjoint(actual), (
            f"{r['candidate_id']}: gap {gap_lower & actual} already in profile"
        )


def test_empty_jd_rejected_with_422(client):
    """Empty JD text is rejected gracefully with a 422, not a 500."""
    resp = client.post("/api/match", json={"jd_text": "", "mode": "ranked"})
    assert resp.status_code == 422


def test_very_long_jd_returns_results(client):
    """A ~5000+ char JD still returns 10 results without error."""
    long_jd = (RANKED_JD + " ") * 60
    assert len(long_jd) > 5000
    resp = client.post("/api/match", json={"jd_text": long_jd, "mode": "ranked"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 10
    assert len(body["results"]) == 10


def test_ranked_results_sorted_by_score_desc(client):
    """Ranked mode orders results by blended score, highest first.

    Regression guard: results used to be returned in raw cross-encoder
    (text-similarity) order, so the visible order ignored the score on each
    card and a zero-skill-match candidate could appear near the top.
    """
    resp = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "ranked"})
    scores = [r["score"] for r in resp.json()["results"]]
    assert scores == sorted(scores, reverse=True), f"not sorted desc: {scores}"


def test_ranked_top_result_has_matched_skills(client):
    """The #1 ranked candidate actually matches JD skills (not a zero-match)."""
    resp = client.post("/api/match", json={"jd_text": RANKED_JD, "mode": "ranked"})
    results = resp.json()["results"]
    assert results[0]["matched"], "top result should have at least one matched skill"


def test_blend_score_skill_match_dominates_semantic():
    """A strong skill match outranks a zero-match with perfect text similarity.

    Deterministic unit check of the blend weighting (no pipeline needed): with
    proficiency fit weighted at 70%, a candidate with zero matched skills can
    no longer be propped up into the top band by semantic similarity alone.
    """
    blend = PipelineOrchestrator._blend_score
    # Zero matched skills (proficiency_fit=0) but maximal semantic similarity.
    zero_match_high_semantic = blend(10.0, 0.0)
    # Full skill match (proficiency_fit=1) with only middling semantic similarity.
    full_match_mid_semantic = blend(0.0, 1.0)
    assert full_match_mid_semantic > zero_match_high_semantic
    # A zero-match score stays in the low band regardless of semantic similarity.
    assert zero_match_high_semantic < 60


SENIOR_DATA_ENGINEER_JD = (
    "Senior Data Engineer: Build petabyte-scale data pipelines. Skills: Data Governance, "
    "Data Analytics, Applications Development, System Integration, Applications Integration, "
    "Data Protection Management."
)

# Tool names only - none exist in the SWDA taxonomy, so nothing is extracted.
NO_FRAMEWORK_JD = "Apache Spark Python SQL Airflow Data Warehousing Cloud Computing Kubernetes Terraform"


def test_senior_data_engineer_top_match_has_skills(client):
    """Regression: the Senior Data Engineer JD no longer tops with a zero-match.

    Previously this sample listed only tool names (Apache Spark, Python, ...) that
    are absent from the taxonomy, so zero skills were extracted, ranking fell
    back to semantic-only text similarity and an engineering profile (Meera Goh,
    cand_118) floated to #1 with "Matched 0 / no gaps - perfect fit". With
    framework skills in the JD, the top result must actually match skills.
    """
    resp = client.post("/api/match", json={"jd_text": SENIOR_DATA_ENGINEER_JD, "mode": "ranked"})
    results = resp.json()["results"]
    assert results[0]["skills_detected"] is True
    assert results[0]["matched"], "top result should have matched framework skills"
    assert results[0]["candidate_id"] != "cand_118", (
        "zero-match engineering profile must not top a data-engineering search"
    )


def test_no_framework_jd_flags_skills_detected_false(client):
    """A JD with no recognizable skills is flagged honestly, not 'perfect fit'."""
    resp = client.post("/api/match", json={"jd_text": NO_FRAMEWORK_JD, "mode": "ranked"})
    results = resp.json()["results"]
    assert results, "pipeline still returns results via semantic/BM25 retrieval"
    for r in results:
        assert r["skills_detected"] is False
        assert r["matched"] == []
        assert r["gap"] == []
