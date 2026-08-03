"""Integration test: the narrative quotes the same score the UI displays.

Runs the full pipeline through the FastAPI TestClient with a fake DashScope
key so the LLM path (not the offline fallback) is exercised. The HTTP client
inside the narrative module is replaced with a stub that echoes each prompt
back as the narrative, so the "{score}% match" figure sent to the LLM can be
compared against the ``score`` field returned for the same candidate.
Hermetic: isolated Qdrant temp store, no network, singleton reset.
"""

import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.pipeline import narrative as narrative_module
from app.pipeline.orchestrator import PipelineOrchestrator

JD = (
    "Account Operations Analyst in finance. Strong Business Planning, Data Governance, "
    "Regulatory Compliance, Quality Assurance and Financial Statements Review required. "
    "Customer account processing, collateral management and ethical culture experience preferred."
)


class EchoAsyncClient:
    """Stub for httpx.AsyncClient that returns the prompt as the completion."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, headers=None, json=None):
        prompt = json["messages"][0]["content"]
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json = MagicMock(
            return_value={"choices": [{"message": {"content": prompt}}]}
        )
        return response


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient with isolated Qdrant, fake API key, and stubbed LLM client."""
    qdrant_dir = tmp_path_factory.mktemp("qdrant_narrative_score")
    orig_qdrant = settings.QDRANT_PATH
    orig_key = settings.DASHSCOPE_API_KEY
    orig_httpx = narrative_module.httpx
    settings.QDRANT_PATH = str(qdrant_dir)
    settings.DASHSCOPE_API_KEY = "test-key"  # force the LLM path
    # Swap only the narrative module's httpx reference so the TestClient's
    # own (real) httpx usage is untouched.
    narrative_module.httpx = SimpleNamespace(AsyncClient=EchoAsyncClient)
    PipelineOrchestrator._instance = None
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        PipelineOrchestrator._instance = None
        settings.QDRANT_PATH = orig_qdrant
        settings.DASHSCOPE_API_KEY = orig_key
        narrative_module.httpx = orig_httpx


@pytest.mark.parametrize("mode", ["ranked", "surprise"])
def test_narrative_score_matches_display_score(client, mode):
    """The % in the narrative prompt equals the result's displayed score."""
    resp = client.post("/api/match", json={"jd_text": JD, "mode": mode})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results, "expected results"
    for r in results:
        match = re.search(r"(\d+)% match", r["narrative"])
        assert match, f"no score in narrative: {r['narrative']!r}"
        assert int(match.group(1)) == r["score"], (
            f"{r['candidate_id']}: narrative says {match.group(1)}%, "
            f"card displays {r['score']}"
        )
        # The prompt (echoed back) must reference this candidate, proving the
        # narrative/score pairing survived any re-ordering.
        assert r["name"] in r["narrative"]
