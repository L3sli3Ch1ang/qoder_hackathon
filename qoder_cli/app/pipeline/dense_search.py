"""Dense vector semantic search module."""

import logging
from pathlib import Path

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.data import get_candidates

logger = logging.getLogger(__name__)

COLLECTION_NAME = "candidates"
VECTOR_SIZE = 384


class DenseSearch:
    """Semantic search using sentence-transformers embeddings + Qdrant Lite."""

    def __init__(self) -> None:
        self._model = SentenceTransformer(settings.MODEL_EMBEDDING)
        self._candidates = get_candidates()

        qdrant_path = Path(settings.QDRANT_PATH)
        qdrant_path.mkdir(parents=True, exist_ok=True)
        self._client = QdrantClient(path=str(qdrant_path))

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection and index candidates if not already present."""
        collections = [c.name for c in self._client.get_collections().collections]
        if COLLECTION_NAME in collections:
            info = self._client.get_collection(COLLECTION_NAME)
            if info.points_count and info.points_count >= len(self._candidates):
                logger.info("Qdrant collection '%s' already indexed (%d points).", COLLECTION_NAME, info.points_count)
                return
            self._client.delete_collection(COLLECTION_NAME)

        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )

        texts = [self._candidate_text(c) for c in self._candidates]
        embeddings = self._model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

        points = [
            models.PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={"candidate_id": c["id"]},
            )
            for i, (c, embedding) in enumerate(zip(self._candidates, embeddings))
        ]
        self._client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info("Indexed %d candidates into Qdrant.", len(points))

    @staticmethod
    def _candidate_text(candidate: dict) -> str:
        """Build text representation for embedding."""
        parts = [
            candidate.get("title", ""),
            candidate.get("sector", ""),
            " ".join(candidate.get("skills", [])),
            candidate.get("summary", ""),
        ]
        return " ".join(parts)

    def run(self, query_text: str) -> list[dict]:
        """Return top-K candidates ranked by cosine similarity.

        Args:
            query_text: Raw JD text to embed and search.

        Returns:
            List of candidate dicts with 'semantic_score' added.
        """
        query_embedding = self._model.encode([query_text], normalize_embeddings=True)[0]

        hits = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=settings.DENSE_TOP_K,
            with_payload=True,
        ).points

        candidate_map = {c["id"]: c for c in self._candidates}
        results = []
        for hit in hits:
            cand_id = hit.payload["candidate_id"]
            candidate = candidate_map.get(cand_id)
            if candidate:
                entry = dict(candidate)
                entry["semantic_score"] = float(hit.score)
                results.append(entry)
        return results
