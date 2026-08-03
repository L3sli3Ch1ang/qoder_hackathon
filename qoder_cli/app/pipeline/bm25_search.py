"""BM25 lexical search module."""

import re

from rank_bm25 import BM25Okapi

from app.config import settings
from app.data import get_candidates


def tokenize(text: str) -> list[str]:
    """Lowercase and split on non-alphanumeric characters."""
    return re.findall(r"[a-z0-9+#]+", text.lower())


class BM25Search:
    """BM25 keyword-based lexical search over candidate profiles."""

    def __init__(self) -> None:
        self._candidates = get_candidates()
        corpus = [self._candidate_text(c) for c in self._candidates]
        self._tokenized_corpus = [tokenize(doc) for doc in corpus]
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    @staticmethod
    def _candidate_text(candidate: dict) -> str:
        """Build searchable text from a candidate profile."""
        parts = [
            candidate.get("title", ""),
            candidate.get("sector", ""),
            " ".join(candidate.get("skills", [])),
            " ".join(candidate.get("certifications", [])),
            candidate.get("summary", ""),
        ]
        return " ".join(parts)

    def run(self, query_tokens: list[str]) -> list[dict]:
        """Return top-K candidates ranked by BM25 score.

        Args:
            query_tokens: Tokenized JD text.

        Returns:
            List of candidate dicts with 'lexical_score' added.
        """
        scores = self._bm25.get_scores(query_tokens)
        scored = list(zip(self._candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for candidate, score in scored[: settings.BM25_TOP_K]:
            entry = dict(candidate)
            entry["lexical_score"] = float(score)
            results.append(entry)
        return results
