"""Unit tests for RRF fusion module."""


def test_rrf_deduplicates():
    """RRF fusion deduplicates candidates appearing in both lists."""
    from app.pipeline.rrf_fusion import RRFFusion

    fusion = RRFFusion()
    keyword = [{"id": "c1", "lexical_score": 5.0}, {"id": "c2", "lexical_score": 4.0}]
    semantic = [{"id": "c1", "semantic_score": 0.9}, {"id": "c3", "semantic_score": 0.8}]

    results = fusion.run(keyword, semantic)
    ids = [r["id"] for r in results]
    assert len(ids) == len(set(ids)), "No duplicates allowed"


def test_rrf_preserves_scores():
    """RRF preserves both lexical and semantic scores."""
    from app.pipeline.rrf_fusion import RRFFusion

    fusion = RRFFusion()
    keyword = [{"id": "c1", "lexical_score": 5.0}]
    semantic = [{"id": "c1", "semantic_score": 0.9}]

    results = fusion.run(keyword, semantic)
    assert results[0]["lexical_score"] == 5.0
    assert results[0]["semantic_score"] == 0.9


def test_rrf_respects_top_k():
    """RRF returns at most RRF_TOP_K results."""
    from app.pipeline.rrf_fusion import RRFFusion
    from app.config import settings

    fusion = RRFFusion()
    keyword = [{"id": f"c{i}", "lexical_score": float(50 - i)} for i in range(50)]
    semantic = [{"id": f"s{i}", "semantic_score": 0.9 - i * 0.01} for i in range(50)]

    results = fusion.run(keyword, semantic)
    assert len(results) <= settings.RRF_TOP_K


def test_rrf_sorted_by_rrf_score():
    """RRF results are sorted by rrf_score descending."""
    from app.pipeline.rrf_fusion import RRFFusion

    fusion = RRFFusion()
    keyword = [{"id": f"c{i}", "lexical_score": float(50 - i)} for i in range(10)]
    semantic = [{"id": f"c{i}", "semantic_score": 0.9 - i * 0.05} for i in range(10)]

    results = fusion.run(keyword, semantic)
    scores = [r["rrf_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
