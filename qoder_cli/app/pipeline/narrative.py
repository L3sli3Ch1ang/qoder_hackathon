"""Narrative generator (LLM) module using Alibaba Cloud Model Studio (DashScope)."""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = (
    "You are a career advisor. In exactly 2 sentences, explain why {candidate_name} "
    "({candidate_title}, {years} years in {sector}) is a {score}% match for "
    "\"{jd_title}\". Their verified transferable skills for this role are: {matched}. "
    "Their single biggest gap is: {gap}. Reference only these skills (do not invent "
    "others). Be specific and encouraging."
)


class NarrativeGenerator:
    """Generate 2-sentence human-readable match explanations via LLM."""

    def __init__(self) -> None:
        self._api_key = settings.DASHSCOPE_API_KEY
        self._model = settings.DASHSCOPE_MODEL
        self._base_url = settings.DASHSCOPE_BASE_URL

    async def run(self, candidate: dict, jd_context: dict, skills: dict, score: int) -> str:
        """Generate a narrative explanation for a single match.

        Args:
            candidate: Candidate profile dict.
            jd_context: Job description context (title, sector).
            skills: Explainability output (matched, gap, bridge).
            score: The blended display score (40-98) shown in the UI, so the
                narrative always quotes the same percentage the card displays.

        Returns:
            A 2-sentence narrative string.
        """
        if not self._api_key:
            return self._fallback_narrative(candidate, jd_context, skills)

        async with httpx.AsyncClient(timeout=15.0) as client:
            return await self._run_one(client, candidate, jd_context, skills, score)

    async def _run_one(
        self,
        client: httpx.AsyncClient,
        candidate: dict,
        jd_context: dict,
        skills: dict,
        score: int,
    ) -> str:
        """Make one DashScope call using an already-open client."""
        # Ground the prompt in the explainability output so the LLM references
        # only skills the candidate actually matched / is missing, instead of
        # inventing plausible-sounding skills from the job title alone.
        matched = skills.get("matched", [])
        gap = skills.get("gap", [])
        matched_text = ", ".join(matched[:4]) if matched else "none specifically verified yet"
        gap_text = gap[0] if gap else "specialized domain knowledge"
        prompt = PROMPT_TEMPLATE.format(
            candidate_name=candidate.get("name", "This candidate"),
            candidate_title=candidate.get("title", "professional"),
            years=candidate.get("years_experience", 5),
            sector=candidate.get("sector", "their field"),
            score=score,
            jd_title=jd_context.get("title", "the role"),
            matched=matched_text,
            gap=gap_text,
        )

        try:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning("DashScope API call failed: %s. Using fallback.", e)
            return self._fallback_narrative(candidate, jd_context, skills)

    async def run_batch(
        self,
        candidates: list[dict],
        jd_context: dict,
        skills_list: list[dict],
        scores: list[int],
    ) -> list[str]:
        """Generate narratives for all candidates concurrently.

        Args:
            candidates: List of candidate dicts.
            jd_context: Shared JD context.
            skills_list: List of explainability outputs per candidate.
            scores: Blended display scores per candidate (same order).

        Returns:
            List of narrative strings.
        """
        # Short-circuit to the offline template when no API key is configured,
        # avoiding a batch of instantly-failing HTTP attempts on every match.
        if not self._api_key:
            return [
                self._fallback_narrative(cand, jd_context, skills)
                for cand, skills in zip(candidates, skills_list)
            ]
        async with httpx.AsyncClient(timeout=15.0) as client:
            tasks = [
                self._run_one(client, cand, jd_context, skills, score)
                for cand, skills, score in zip(candidates, skills_list, scores)
            ]
            return await asyncio.gather(*tasks)

    @staticmethod
    def _fallback_narrative(candidate: dict, jd_context: dict, skills: dict) -> str:
        """Generate a template-based narrative when LLM is unavailable."""
        name = candidate.get("name", "This candidate")
        title = candidate.get("title", "professional")
        sector = candidate.get("sector", "their field")
        years = candidate.get("years_experience", 5)
        jd_title = jd_context.get("title", "this role")

        matched = skills.get("matched", [])
        gap = skills.get("gap", [])

        if matched:
            strengths = ", ".join(matched[:3])
        else:
            # No framework skill matched: reference the candidate's REAL profile
            # skills so the narrative stays consistent with the full profile
            # (never invents skills they do not have).
            own_skills = candidate.get("skills", [])[:3]
            strengths = ", ".join(own_skills) if own_skills else "diverse transferable skills"
        gap_text = gap[0] if gap else "specialized domain knowledge"

        return (
            f"{name} brings {years} years as a {title} in {sector}, "
            f"with strong transferable skills in {strengths} that align well with {jd_title}. "
            f"Their primary development area is {gap_text}, which can be bridged through targeted upskilling."
        )
