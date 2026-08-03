"""Unit tests for dense vector semantic search (Qdrant Lite).

These tests run against an isolated temporary Qdrant store so they never
fight the dev server's file lock on ``./qdrant_data``. The embedding model
is loaded once per module via a module-scoped fixture.
"""

import pytest

from app.config import settings
from app.pipeline import dense_search as dense_module


@pytest.fixture(scope="module")
def searcher(tmp_path_factory):
    """Build one DenseSearch against an isolated store (indexes once)."""
    qdrant_dir = tmp_path_factory.mktemp("qdrant_dense_test")
    original = settings.QDRANT_PATH
    settings.QDRANT_PATH = str(qdrant_dir)
    try:
        instance = dense_module.DenseSearch()
        yield instance
        instance._client.close()
    finally:
        settings.QDRANT_PATH = original


def test_vector_size_is_384():
    """The collection is configured for 384-dim MiniLM embeddings."""
    assert dense_module.VECTOR_SIZE == 384


def test_embedding_dimension_is_384(searcher):
    """The loaded embedding model actually produces 384-dim vectors."""
    vector = searcher._model.encode(["software engineer"], normalize_embeddings=True)[0]
    assert len(vector) == 384


def test_collection_indexed_all_candidates(searcher):
    """All 150 candidates are indexed into the collection."""
    info = searcher._client.get_collection(dense_module.COLLECTION_NAME)
    assert info.points_count == len(searcher._candidates) == 150


def test_run_returns_results_with_semantic_score(searcher):
    """Each result carries a float semantic_score and candidate id."""
    results = searcher.run("Risk Assessment Data Analytics Python Machine Learning")
    assert len(results) > 0
    assert len(results) <= settings.DENSE_TOP_K
    for r in results:
        assert "semantic_score" in r
        assert isinstance(r["semantic_score"], float)
        assert "id" in r


def test_run_results_sorted_descending(searcher):
    """Dense results are sorted by semantic_score descending."""
    results = searcher.run("Financial Modeling Valuation Python")
    scores = [r["semantic_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_collection_reused_not_reindexed(tmp_path, monkeypatch):
    """A second init on an already-indexed store skips re-encoding."""
    original = settings.QDRANT_PATH
    settings.QDRANT_PATH = str(tmp_path)
    try:
        # First instance indexes the corpus from scratch.
        first = dense_module.DenseSearch()
        first._client.close()

        # Spy on encode: the reuse path must NOT re-encode the corpus.
        calls: list = []
        real_encode = dense_module.SentenceTransformer.encode

        def spy_encode(self, *args, **kwargs):
            calls.append(args)
            return real_encode(self, *args, **kwargs)

        monkeypatch.setattr(dense_module.SentenceTransformer, "encode", spy_encode)

        second = dense_module.DenseSearch()
        info = second._client.get_collection(dense_module.COLLECTION_NAME)
        second._client.close()

        assert info.points_count == 150
        assert calls == []  # no re-indexing happened
    finally:
        settings.QDRANT_PATH = original
