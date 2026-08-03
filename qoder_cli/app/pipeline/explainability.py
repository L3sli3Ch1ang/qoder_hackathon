"""Explainability engine module."""

from app.data import get_bridges, get_all_skills


class ExplainabilityEngine:
    """Skill extraction, gap analysis, and bridge-skill mapping."""

    def __init__(self) -> None:
        self._bridges = get_bridges()
        self._all_skills = get_all_skills()
        # Build lowercase lookup for matching
        self._skill_lookup = {s.lower(): s for s in self._all_skills}

    def extract_skills(self, text: str) -> list[str]:
        """Extract known skills from free text using taxonomy matching.

        Args:
            text: Raw text (e.g., job description).

        Returns:
            List of recognized skill names.
        """
        text_lower = text.lower()
        found = []
        for skill_lower, skill_canonical in self._skill_lookup.items():
            if skill_lower in text_lower:
                found.append(skill_canonical)
        return found

    def run(
        self,
        jd_skills: list[str],
        candidate_skills: list[str],
        required_levels: dict[str, int] | None = None,
        candidate_levels: dict[str, int] | None = None,
    ) -> dict:
        """Compare JD and candidate skills to produce matched/gap/bridge arrays.

        When ``required_levels`` (skill -> required proficiency 1-6) and
        ``candidate_levels`` (skill -> candidate proficiency 1-6) are supplied,
        also produces:
          * ``matched_detail``: per matched skill, the required vs candidate
            proficiency level and whether the candidate meets it (``met``);
          * ``proficiency_fit``: weighted coverage of the required skills in
            [0, 1] (full credit if met, partial ``cand_pl/req_pl`` if the skill
            is present below the required level, 0 if absent), or ``None`` when
            no required levels are available to evaluate.

        Args:
            jd_skills: Extracted skills from the job description.
            candidate_skills: Skills listed in the candidate profile.
            required_levels: Optional required proficiency per JD skill (1-6).
            candidate_levels: Optional candidate proficiency per skill (1-6).

        Returns:
            Dict with keys: matched, gap, bridge, matched_detail, proficiency_fit.
        """
        cand_set = set(candidate_skills)

        # Case-insensitive matching
        cand_lower = {s.lower(): s for s in cand_set}
        matched = []
        gap = []

        for skill in jd_skills:
            if skill.lower() in cand_lower:
                matched.append(skill)
            else:
                gap.append(skill)

        # Bridge mapping: for each gap skill, check if candidate has an adjacent skill
        bridge = []
        for gap_skill in gap:
            bridge_info = self._bridges.get(gap_skill)
            if bridge_info:
                via_skill = bridge_info["via"]
                # Check if candidate has the bridging skill
                if via_skill.lower() in cand_lower:
                    bridge.append({
                        "gap_skill": gap_skill,
                        "via_skill": via_skill,
                        "confidence": bridge_info["confidence"],
                    })

        matched_detail, proficiency_fit = self._proficiency_analysis(
            jd_skills, cand_lower, required_levels or {}, candidate_levels or {}
        )

        return {
            "matched": matched,
            "gap": gap,
            "bridge": bridge,
            "matched_detail": matched_detail,
            "proficiency_fit": proficiency_fit,
        }

    @staticmethod
    def _proficiency_analysis(
        jd_skills: list[str],
        cand_lower: dict[str, str],
        required_levels: dict[str, int],
        candidate_levels: dict[str, int],
    ) -> tuple[list[dict], float | None]:
        """Build per-skill proficiency detail and an overall fit score.

        Returns (matched_detail, proficiency_fit). ``proficiency_fit`` is None
        when no JD skill has a required level to evaluate against.
        """
        cand_levels_lower = {k.lower(): v for k, v in candidate_levels.items()}
        matched_detail: list[dict] = []
        credits: list[float] = []

        for skill in jd_skills:
            req_pl = required_levels.get(skill)
            has_skill = skill.lower() in cand_lower
            cand_pl = cand_levels_lower.get(skill.lower())

            if has_skill:
                met = (req_pl is None or cand_pl is None) or (cand_pl >= req_pl)
                matched_detail.append({
                    "skill": skill,
                    "required_pl": req_pl,
                    "candidate_pl": cand_pl,
                    "met": met,
                })

            if req_pl is None:
                continue  # not evaluated for fit
            if has_skill:
                if cand_pl is None:
                    credits.append(1.0)  # matched, level unknown -> full credit
                else:
                    credits.append(1.0 if cand_pl >= req_pl else cand_pl / req_pl)
            else:
                credits.append(0.0)

        proficiency_fit = round(sum(credits) / len(credits), 3) if credits else None
        return matched_detail, proficiency_fit
