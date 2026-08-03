"""Unit tests for BM25 search module."""

import pytest


def test_bm25_index_builds():
    """BM25 index builds successfully over all candidates."""
    from app.pipeline.bm25_search import BM25Search

    searcher = BM25Search()
    assert searcher._bm25 is not None
    assert len(searcher._candidates) == 150


def test_bm25_returns_results():
    """BM25 returns non-empty top-50 for a sample query."""
    from app.pipeline.bm25_search import BM25Search, tokenize

    searcher = BM25Search()
    tokens = tokenize("Risk Assessment Data Analytics Python Machine Learning")
    results = searcher.run(tokens)
    assert len(results) > 0
    assert len(results) <= 50


def test_bm25_results_have_scores():
    """Each BM25 result has a lexical_score field."""
    from app.pipeline.bm25_search import BM25Search, tokenize

    searcher = BM25Search()
    tokens = tokenize("Financial Modeling Valuation Python")
    results = searcher.run(tokens)
    for r in results:
        assert "lexical_score" in r
        assert isinstance(r["lexical_score"], float)


def test_bm25_results_sorted_descending():
    """BM25 results are sorted by score descending."""
    from app.pipeline.bm25_search import BM25Search, tokenize

    searcher = BM25Search()
    tokens = tokenize("Cybersecurity Cloud Security Risk Assessment")
    results = searcher.run(tokens)
    scores = [r["lexical_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_tokenize():
    """Tokenizer lowercases and splits correctly."""
    from app.pipeline.bm25_search import tokenize

    tokens = tokenize("Python C++ Machine Learning")
    assert "python" in tokens
    assert "c++" in tokens
    assert "machine" in tokens
    assert "learning" in tokens
