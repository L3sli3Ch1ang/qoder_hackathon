"""Sector convergence — precomputed pairwise skill overlap between sectors.

Implements the spec's "Sector Convergence" component: pairwise Jaccard
similarity between the five sector skill sets (from the skill taxonomy).
The values power the convergence strip on the landing page and are computed
once (precomputed) rather than hardcoded.
"""

from app.data import get_skill_taxonomy

# Sector metadata keyed by the lowercase sector id used throughout the data
# (candidates.json, skill_taxonomy.json). `label` is the display name,
# `short` is the compact abbreviation used in the convergence strip.
SECTOR_META = {
    "finance": {"label": "Finance", "short": "fin"},
    "ict": {"label": "ICT", "short": "ict"},
    "healthcare": {"label": "Healthcare", "short": "health"},
    "engineering": {"label": "Engineering", "short": "eng"},
    "sustainability": {"label": "Sustainability", "short": "sust"},
}


class SectorConvergence:
    """Precompute pairwise Jaccard similarity between sector skill sets."""

    def __init__(self) -> None:
        taxonomy = get_skill_taxonomy()
        self._sets: dict[str, set[str]] = {
            sector: set(skills) for sector, skills in taxonomy.items()
        }

    @staticmethod
    def jaccard(a: set[str], b: set[str]) -> float:
        """Jaccard index |A ∩ B| / |A ∪ B|; 0.0 when both sets are empty."""
        union = a | b
        if not union:
            return 0.0
        return len(a & b) / len(union)

    def run(self) -> list[dict]:
        """Return every sector pair sorted by overlap (descending).

        Each entry carries the sector ids (a, b), display labels, compact
        abbreviations, the raw score (0-1) and an integer percentage.
        """
        sectors = sorted(self._sets.keys())
        pairs: list[dict] = []
        for i in range(len(sectors)):
            for j in range(i + 1, len(sectors)):
                a, b = sectors[i], sectors[j]
                score = self.jaccard(self._sets[a], self._sets[b])
                meta_a = SECTOR_META.get(a, {"label": a.title(), "short": a[:4]})
                meta_b = SECTOR_META.get(b, {"label": b.title(), "short": b[:4]})
                pairs.append({
                    "a": a,
                    "b": b,
                    "label_a": meta_a["label"],
                    "label_b": meta_b["label"],
                    "short_a": meta_a["short"],
                    "short_b": meta_b["short"],
                    "score": round(score, 4),
                    "pct": int(round(score * 100)),
                })
        pairs.sort(key=lambda p: p["score"], reverse=True)
        return pairs
