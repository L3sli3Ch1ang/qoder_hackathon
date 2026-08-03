"""Pipeline orchestrator — initializes and coordinates all pipeline stages."""

import logging
import re

from app.data import get_all_skills, get_jobs, get_skill_registry
from app.pipeline.bm25_search import BM25Search, tokenize
from app.pipeline.dense_search import DenseSearch
from app.pipeline.rrf_fusion import RRFFusion
from app.pipeline.reranker import CrossEncoderReranker
from app.pipeline.explainability import ExplainabilityEngine
from app.pipeline.surprise_filter import SurpriseFilter
from app.pipeline.narrative import NarrativeGenerator
from app.pipeline.course_mapper import CourseMapper

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Singleton orchestrator that runs the full matching pipeline."""

    _instance: "PipelineOrchestrator | None" = None

    def __init__(self) -> None:
        logger.info("Initializing pipeline components...")
        self.bm25 = BM25Search()
        self.dense = DenseSearch()
        self.rrf = RRFFusion()
        self.reranker = CrossEncoderReranker()
        self.explainability = ExplainabilityEngine()
        self.surprise_filter = SurpriseFilter()
        self.narrative = NarrativeGenerator()
        self.course_mapper = CourseMapper()
        self._registry = get_skill_registry()
        logger.info("Pipeline initialization complete.")

    @classmethod
    def get_instance(cls) -> "PipelineOrchestrator":
        """Get or create the singleton orchestrator instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def match(
        self,
        jd_text: str,
        mode: str = "ranked",
        added_skills: list[str] | None = None,
        removed_skills: list[str] | None = None,
    ) -> list[dict]:
        """Run the full matching pipeline.

        Args:
            jd_text: Raw job description text.
            mode: 'ranked' or 'surprise'.
            added_skills: Skills to add (What-If explorer).
            removed_skills: Skills to remove (What-If explorer).

        Returns:
            List of top-10 result dicts with all enrichment data.
        """
        # Apply What-If skill modifications
        effective_text = jd_text
        if added_skills:
            effective_text += " " + " ".join(added_skills)
        if removed_skills:
            for skill in removed_skills:
                effective_text = self._remove_skill_mentions(effective_text, skill)

        # Stage 1 & 2: BM25 + Dense search
        query_tokens = tokenize(effective_text)
        keyword_results = self.bm25.run(query_tokens)
        semantic_results = self.dense.run(effective_text)

        # Stage 3: RRF Fusion
        fused = self.rrf.run(keyword_results, semantic_results)

        # Stage 4: Cross-encoder re-ranking
        top_candidates = self.reranker.run(effective_text, fused)

        # Stage 5: Explainability (proficiency-aware)
        jd_skills = self.explainability.extract_skills(effective_text)
        if removed_skills:
            # extract_skills substring-matches, so a removed skill can still be
            # found inside a longer, distinct skill title (e.g. "Risk
            # Management" inside "Credit Risk Management") — drop it explicitly.
            removed_lower = {s.lower() for s in removed_skills}
            jd_skills = [s for s in jd_skills if s.lower() not in removed_lower]
        required_levels = self._resolve_required_levels(effective_text, jd_skills)
        skills_list = []
        for candidate in top_candidates:
            skills = self.explainability.run(
                jd_skills,
                candidate.get("skills", []),
                required_levels=required_levels,
                candidate_levels=candidate.get("skill_levels", {}),
            )
            skills_list.append(skills)
            candidate["skills_analysis"] = skills

        # Stage 6: Surprise filter (if mode=surprise)
        if mode == "surprise":
            top_candidates = self.surprise_filter.run(top_candidates)
            # Rebuild skills_list from each candidate's own analysis so skills
            # stay aligned with the correct candidate after re-ordering.
            skills_list = [c["skills_analysis"] for c in top_candidates]

        # Hybrid display score: blend semantic relevance (cross-encoder) with
        # structured proficiency fit. Computed before narrative generation so
        # the narrative quotes the same percentage the card displays.
        display_scores = [
            self._blend_score(
                candidate.get("cross_encoder_score", 0.0),
                skills.get("proficiency_fit"),
            )
            for candidate, skills in zip(top_candidates, skills_list)
        ]

        # Stage 7: Narrative generation (parallel)
        jd_context = {"title": self._extract_jd_title(jd_text), "sector": ""}
        narratives = await self.narrative.run_batch(
            top_candidates, jd_context, skills_list, display_scores
        )

        # Stage 8: Course mapping
        skills_detected = bool(jd_skills)
        results = []
        for candidate, skills, narrative, display_score in zip(
            top_candidates, skills_list, narratives, display_scores
        ):
            courses = self.course_mapper.run(skills.get("gap", []))

            # Surface official Emerging / CASL signals for the relevant skills.
            relevant = skills.get("matched", []) + skills.get("gap", [])
            emerging_skills = [s for s in relevant if self._registry.get(s, {}).get("emerging")]
            casl_skills = [s for s in relevant if self._registry.get(s, {}).get("casl")]

            results.append({
                "candidate_id": candidate["id"],
                "name": candidate.get("name", ""),
                "title": candidate.get("title", ""),
                "sector": candidate.get("sector", ""),
                "years_experience": candidate.get("years_experience", 0),
                "score": display_score,
                "narrative": narrative,
                "matched": skills.get("matched", []),
                "gap": skills.get("gap", []),
                "bridge": skills.get("bridge", []),
                "courses": courses,
                "is_surprise": candidate.get("is_surprise", False),
                "proficiency_fit": skills.get("proficiency_fit"),
                "matched_detail": skills.get("matched_detail", []),
                "emerging_skills": emerging_skills,
                "casl_skills": casl_skills,
                "skills_detected": skills_detected,
            })

        # Final ordering: in ranked mode the displayed order must follow the
        # blended score (skill match dominates), not the raw cross-encoder text
        # similarity that produced the top-K. Without this, a candidate whose
        # profile text merely resembles the JD can outrank one who actually has
        # the matched skills. Surprise mode keeps its serendipity ordering from
        # the surprise filter. Stable sort => cross-encoder order breaks ties.
        if mode != "surprise":
            results.sort(key=lambda r: r["score"], reverse=True)

        return results

    @staticmethod
    def _remove_skill_mentions(text: str, skill: str) -> str:
        """Remove standalone mentions of ``skill`` from ``text`` (What-If).

        Case-insensitive like ``extract_skills``. Occurrences that sit inside
        a longer, distinct taxonomy skill title (e.g. "Risk Management" within
        "Credit Risk Management") are preserved — those are different skills.
        """
        skill_lower = skill.lower()
        longer_titles = [
            s for s in get_all_skills()
            if skill_lower in s.lower() and s.lower() != skill_lower
        ]
        protected: list[tuple[int, int]] = []
        for title in longer_titles:
            for m in re.finditer(re.escape(title), text, flags=re.IGNORECASE):
                protected.append(m.span())

        def replace(m: re.Match) -> str:
            if any(a <= m.start() and m.end() <= b for a, b in protected):
                return m.group(0)
            return ""

        return re.sub(
            rf"(?<![a-zA-Z0-9]){re.escape(skill)}(?![a-zA-Z0-9])",
            replace,
            text,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _blend_score(raw: float, proficiency_fit: float | None) -> int:
        """Blend the cross-encoder semantic score with proficiency fit (0-100).

        The cross-encoder score (typically -10..+10) is normalized to [0, 1];
        when a proficiency fit is available the final score is 30% semantic +
        70% proficiency fit, mapped to the 40-98 display range. Actual skill
        match dominates so a candidate with zero matched skills cannot be
        propped up by text similarity alone. Falls back to semantic-only when
        proficiency fit is unavailable.
        """
        semantic_norm = max(0.0, min(1.0, (raw + 10.0) / 20.0))
        if proficiency_fit is None:
            combined = semantic_norm
        else:
            combined = 0.3 * semantic_norm + 0.7 * max(0.0, min(1.0, proficiency_fit))
        return int(40 + combined * 58)

    def _resolve_required_levels(
        self, jd_text: str, jd_skills: list[str]
    ) -> dict[str, int]:
        """Resolve a required proficiency level (1-6) for each extracted JD skill.

        Every extracted skill is guaranteed a level so that What-If additions
        always influence the proficiency fit. Strategy (deterministic):
          1. Start from a seniority-inferred baseline applied to every skill.
          2. If a specific seeded job title is mentioned, overlay that job's
             authoritative SWDA-derived ``skill_requirements`` for the skills
             it actually requires (the rest keep the seniority baseline).

        Regression guard: the previous implementation returned only the
        matched job's requirements when any overlapped, silently dropping
        every other skill (notably What-If additions) out of the fit.
        """
        if not jd_skills:
            return {}
        base = self._seniority_level(jd_text)
        levels = {skill: base for skill in jd_skills}
        best = self._match_seeded_job(jd_text)
        if best is not None:
            req = best.get("skill_requirements", {})
            for skill in jd_skills:
                if skill in req:
                    levels[skill] = req[skill]
        return levels

    @staticmethod
    def _match_seeded_job(jd_text: str) -> dict | None:
        """Return the most specific seeded job whose title is mentioned in the JD.

        Uses word-boundary matching and ignores single-word generic titles
        (e.g. "Engineer", "Executive") that would otherwise match inside a
        longer, distinct role title such as "Senior Data Engineer" and pull in
        the wrong job's skill requirements.
        """
        text_lower = jd_text.lower()
        best = None
        best_len = 0
        for job in get_jobs():
            title = job.get("title", "").strip()
            if len(title.split()) < 2:
                continue  # too generic to identify a specific role
            pattern = rf"(?<![a-z0-9]){re.escape(title.lower())}(?![a-z0-9])"
            if re.search(pattern, text_lower) and len(title) > best_len:
                best = job
                best_len = len(title)
        return best

    @staticmethod
    def _seniority_level(text: str) -> int:
        """Infer a required proficiency level (1-6) from seniority cues."""
        t = text.lower()
        if any(w in t for w in ("director", "head of", "chief", "c-level", "cxo", "vice president", "partner")):
            return 6
        if any(w in t for w in ("manager", "principal", "lead")):
            return 5
        if any(w in t for w in ("senior", "staff", "experienced")):
            return 4
        if any(w in t for w in ("junior", "associate", "assistant", "intern", "graduate", "entry", "trainee")):
            return 2
        return 3

    @staticmethod
    def _extract_jd_title(jd_text: str) -> str:
        """Extract a title from JD text (first line or first 80 chars)."""
        first_line = jd_text.strip().split("\n")[0].strip()
        # Drop any inline "Skills: ..." list so the narrative quotes a clean role
        # title (e.g. "Senior Data Engineer") rather than the raw skills dump.
        first_line = re.split(r"\s+Skills?:", first_line, flags=re.IGNORECASE)[0].strip()
        # Avoid a double full-stop when the narrative appends its own sentence
        # ending (the cleaned title often keeps the intro sentence's period).
        first_line = first_line.rstrip(". ")
        if len(first_line) <= 80:
            return first_line
        return first_line[:77] + "..."
