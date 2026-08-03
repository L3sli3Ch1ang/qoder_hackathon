"""Scaffold verification tests for SkillBridge Phase 1."""

import pytest
from fastapi.testclient import TestClient


def test_imports():
    """All pipeline modules and config import without error."""
    from app.config import settings  # noqa: F401
    from app.pipeline.bm25_search import BM25Search  # noqa: F401
    from app.pipeline.dense_search import DenseSearch  # noqa: F401
    from app.pipeline.rrf_fusion import RRFFusion  # noqa: F401
    from app.pipeline.reranker import CrossEncoderReranker  # noqa: F401
    from app.pipeline.explainability import ExplainabilityEngine  # noqa: F401
    from app.pipeline.surprise_filter import SurpriseFilter  # noqa: F401
    from app.pipeline.narrative import NarrativeGenerator  # noqa: F401
    from app.pipeline.course_mapper import CourseMapper  # noqa: F401


def test_config_loads():
    """Settings singleton has expected non-empty values."""
    from app.config import settings

    assert isinstance(settings.MODEL_EMBEDDING, str) and settings.MODEL_EMBEDDING
    assert isinstance(settings.MODEL_RERANKER, str) and settings.MODEL_RERANKER
    assert isinstance(settings.QDRANT_PATH, str) and settings.QDRANT_PATH
    assert isinstance(settings.SEED_DATA_PATH, str) and settings.SEED_DATA_PATH


def test_app_starts():
    """FastAPI app object is created and TestClient can be instantiated."""
    from app.main import app

    assert app is not None
    client = TestClient(app)
    assert client is not None


def test_health_endpoint():
    """GET /health returns 200 with {"status": "ok"}."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
