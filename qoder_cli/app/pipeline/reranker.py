"""Cross-encoder re-ranking module."""

from sentence_transformers import CrossEncoder

from app.config import settings


class CrossEncoderReranker:
    """Re-rank fused candidates using a cross-encoder model."""

    def __init__(self) -> None:
        self._model = CrossEncoder(settings.MODEL_RERANKER)

    def run(self, jd_text: str, candidates: list[dict]) -> list[dict]:
        """Score (JD, candidate) pairs and return top-K re-ranked.

        Args:
            jd_text: Raw job description text.
            candidates: Top-30 fused candidates.

        Returns:
            Top-10 candidates sorted by cross-encoder relevance score.
        """
        if not candidates:
            return []

        pairs = [(jd_text, self._candidate_text(c)) for c in candidates]
        scores = self._model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["cross_encoder_score"] = float(score)

        ranked = sorted(candidates, key=lambda x: x["cross_encoder_score"], reverse=True)
        return ranked[: settings.RERANK_TOP_K]

    @staticmethod
    def _candidate_text(candidate: dict) -> str:
        """Build text representation for cross-encoder scoring."""
        parts = [
            candidate.get("title", ""),
            " ".join(candidate.get("skills", [])),
            candidate.get("summary", ""),
        ]
        return " ".join(parts)
