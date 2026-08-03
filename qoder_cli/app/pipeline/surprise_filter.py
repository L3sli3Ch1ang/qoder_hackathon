"""Surprise filter (serendipity mode) module."""

EPSILON = 1e-6


class SurpriseFilter:
    """Re-sort results by semantic/lexical ratio to surface non-obvious matches."""

    def run(self, candidates: list[dict]) -> list[dict]:
        """Sort candidates by surprise_score = semantic_score / (lexical_score + epsilon).

        Args:
            candidates: Top-10 candidates with semantic and lexical scores.

        Returns:
            Re-ordered list with is_surprise flag set to True.
        """
        for candidate in candidates:
            semantic = candidate.get("semantic_score", 0.0)
            lexical = candidate.get("lexical_score", 0.0)
            candidate["surprise_score"] = semantic / (lexical + EPSILON)
            candidate["is_surprise"] = True

        ranked = sorted(candidates, key=lambda x: x["surprise_score"], reverse=True)
        return ranked
