"""Tests for the candidate CV/profile detail endpoint (GET /api/candidate/{id}).

Deliberately lightweight: the TestClient is used *without* a context manager so
the app lifespan (which loads the heavy ML pipeline) is skipped. This endpoint
only reads candidates.json, so no models or Qdrant store are needed.
"""

from fastapi.testclient import TestClient

from app.data import get_candidate_by_id
from app.main import app

client = TestClient(app)


def test_get_candidate_by_id_helper():
    """Data helper returns the record for a known id and None for an unknown one."""
    cand = get_candidate_by_id("cand_001")
    assert cand is not None
    assert cand["id"] == "cand_001"
    assert get_candidate_by_id("cand_does_not_exist") is None


def test_candidate_profile_returns_full_record():
    """The endpoint returns the full structured profile behind a match result."""
    resp = client.get("/api/candidate/cand_001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "cand_001"
    assert body["name"]
    assert body["sector"]
    assert body["title"]
    assert isinstance(body["years_experience"], int)
    assert isinstance(body["skills"], list) and body["skills"]
    assert isinstance(body["skill_levels"], dict) and body["skill_levels"]
    assert isinstance(body["certifications"], list)
    assert isinstance(body["summary"], str) and body["summary"]
    # Proficiency levels are keyed by skills the candidate actually has.
    assert set(body["skill_levels"].keys()).issubset(set(body["skills"]))


def test_candidate_profile_unknown_id_returns_404():
    """An unknown candidate id yields a clean 404, not a 500."""
    resp = client.get("/api/candidate/cand_does_not_exist")
    assert resp.status_code == 404
