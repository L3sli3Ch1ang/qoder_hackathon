"""Unit tests for surprise filter module."""


def test_surprise_filter_reorders():
    """Surprise filter re-orders by semantic/lexical ratio."""
    from app.pipeline.surprise_filter import SurpriseFilter

    sf = SurpriseFilter()
    candidates = [
        {"id": "c1", "semantic_score": 0.9, "lexical_score": 5.0},
        {"id": "c2", "semantic_score": 0.85, "lexical_score": 0.5},
        {"id": "c3", "semantic_score": 0.7, "lexical_score": 3.0},
    ]

    results = sf.run(candidates)
    # c2 has highest ratio (0.85/0.5) so should be first
    assert results[0]["id"] == "c2"


def test_surprise_filter_sets_flag():
    """Surprise filter sets is_surprise=True on all results."""
    from app.pipeline.surprise_filter import SurpriseFilter

    sf = SurpriseFilter()
    candidates = [
        {"id": "c1", "semantic_score": 0.9, "lexical_score": 1.0},
        {"id": "c2", "semantic_score": 0.8, "lexical_score": 2.0},
    ]

    results = sf.run(candidates)
    for r in results:
        assert r["is_surprise"] is True


def test_surprise_filter_computes_score():
    """Surprise filter adds surprise_score field."""
    from app.pipeline.surprise_filter import SurpriseFilter

    sf = SurpriseFilter()
    candidates = [{"id": "c1", "semantic_score": 0.9, "lexical_score": 1.0}]

    results = sf.run(candidates)
    assert "surprise_score" in results[0]
    assert results[0]["surprise_score"] > 0


def test_surprise_filter_handles_zero_lexical():
    """Surprise filter handles zero lexical score without division error."""
    from app.pipeline.surprise_filter import SurpriseFilter

    sf = SurpriseFilter()
    candidates = [{"id": "c1", "semantic_score": 0.9, "lexical_score": 0.0}]

    results = sf.run(candidates)
    assert results[0]["surprise_score"] > 0
