"""Reciprocal Rank Fusion module."""

from app.config import settings


class RRFFusion:
    """Merge BM25 and dense vector ranked lists using RRF (k=60)."""

    def run(self, keyword_results: list[dict], semantic_results: list[dict]) -> list[dict]:
        """Fuse two ranked lists into a deduplicated top-K.

        Args:
            keyword_results: Top-50 from BM25 search (must have 'lexical_score').
            semantic_results: Top-50 from dense vector search (must have 'semantic_score').

        Returns:
            Top-30 candidates sorted by RRF score with both scores preserved.
        """
        k = settings.RRF_K
        scores: dict[str, float] = {}
        candidate_data: dict[str, dict] = {}

        # Score from keyword ranking
        for rank, candidate in enumerate(keyword_results, start=1):
            cid = candidate["id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            if cid not in candidate_data:
                candidate_data[cid] = dict(candidate)
            candidate_data[cid]["lexical_score"] = candidate.get("lexical_score", 0.0)

        # Score from semantic ranking
        for rank, candidate in enumerate(semantic_results, start=1):
            cid = candidate["id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            if cid not in candidate_data:
                candidate_data[cid] = dict(candidate)
            candidate_data[cid]["semantic_score"] = candidate.get("semantic_score", 0.0)

        # Ensure both scores exist on every candidate
        for cid, data in candidate_data.items():
            data.setdefault("lexical_score", 0.0)
            data.setdefault("semantic_score", 0.0)
            data["rrf_score"] = scores[cid]

        # Sort by RRF score descending, take top-K
        ranked = sorted(candidate_data.values(), key=lambda x: x["rrf_score"], reverse=True)
        return ranked[: settings.RRF_TOP_K]
