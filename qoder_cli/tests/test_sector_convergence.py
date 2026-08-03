"""Unit tests for the SectorConvergence component (pairwise Jaccard)."""


def test_jaccard_identical_sets():
    """Identical non-empty sets have Jaccard index 1.0."""
    from app.pipeline.sector_convergence import SectorConvergence

    assert SectorConvergence.jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_disjoint_sets():
    """Disjoint sets have Jaccard index 0.0."""
    from app.pipeline.sector_convergence import SectorConvergence

    assert SectorConvergence.jaccard({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_partial_overlap():
    """Partial overlap computes |A∩B| / |A∪B| correctly."""
    from app.pipeline.sector_convergence import SectorConvergence

    # intersection = {b, c} (2), union = {a, b, c, d} (4) -> 0.5
    assert SectorConvergence.jaccard({"a", "b", "c"}, {"b", "c", "d"}) == 0.5


def test_jaccard_empty_sets():
    """Two empty sets return 0.0 (no division by zero)."""
    from app.pipeline.sector_convergence import SectorConvergence

    assert SectorConvergence.jaccard(set(), set()) == 0.0
    assert SectorConvergence.jaccard({"a"}, set()) == 0.0


def test_run_returns_all_pairs():
    """Five sectors yield exactly C(5,2) = 10 unordered pairs."""
    from app.pipeline.sector_convergence import SectorConvergence

    pairs = SectorConvergence().run()
    assert len(pairs) == 10


def test_run_pairs_are_unique_and_distinct():
    """Each pair has two distinct sectors and no pair is repeated."""
    from app.pipeline.sector_convergence import SectorConvergence

    pairs = SectorConvergence().run()
    seen = set()
    for p in pairs:
        assert p["a"] != p["b"]
        key = frozenset((p["a"], p["b"]))
        assert key not in seen, f"duplicate pair {key}"
        seen.add(key)


def test_run_pairs_use_taxonomy_sectors():
    """Pair sector ids come from the skill taxonomy keys."""
    from app.pipeline.sector_convergence import SectorConvergence
    from app.data import get_skill_taxonomy

    sectors = set(get_skill_taxonomy().keys())
    for p in SectorConvergence().run():
        assert p["a"] in sectors
        assert p["b"] in sectors


def test_run_sorted_descending_by_score():
    """Pairs are returned sorted by score, highest first."""
    from app.pipeline.sector_convergence import SectorConvergence

    scores = [p["score"] for p in SectorConvergence().run()]
    assert scores == sorted(scores, reverse=True)


def test_run_scores_in_unit_range():
    """Scores lie in [0, 1] and pct in [0, 100]."""
    from app.pipeline.sector_convergence import SectorConvergence

    for p in SectorConvergence().run():
        assert 0.0 <= p["score"] <= 1.0
        assert 0 <= p["pct"] <= 100


def test_run_score_matches_jaccard_of_sets():
    """Each reported score equals the Jaccard of the underlying skill sets."""
    from app.pipeline.sector_convergence import SectorConvergence
    from app.data import get_skill_taxonomy

    taxonomy = get_skill_taxonomy()
    conv = SectorConvergence()
    for p in conv.run():
        expected = conv.jaccard(set(taxonomy[p["a"]]), set(taxonomy[p["b"]]))
        assert abs(p["score"] - round(expected, 4)) < 1e-9


def test_run_pct_consistent_with_score():
    """pct is the rounded percentage of score."""
    from app.pipeline.sector_convergence import SectorConvergence

    for p in SectorConvergence().run():
        assert p["pct"] == int(round(p["score"] * 100))


def test_run_carries_display_metadata():
    """Each pair carries non-empty labels and short abbreviations."""
    from app.pipeline.sector_convergence import SectorConvergence

    for p in SectorConvergence().run():
        assert p["label_a"] and p["label_b"]
        assert p["short_a"] and p["short_b"]
