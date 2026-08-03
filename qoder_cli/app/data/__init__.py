"""Seed data loader for SkillBridge."""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def get_candidates() -> list[dict]:
    """Load all 150 candidate profiles."""
    with open(DATA_DIR / "candidates.json", encoding="utf-8") as f:
        return json.load(f)


def get_candidate_by_id(candidate_id: str) -> dict | None:
    """Return a single candidate profile by id, or None if not found."""
    for candidate in get_candidates():
        if candidate.get("id") == candidate_id:
            return candidate
    return None


@lru_cache(maxsize=1)
def get_jobs() -> list[dict]:
    """Load all 30 job descriptions."""
    with open(DATA_DIR / "jobs.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_courses() -> dict:
    """Load course mappings (skill -> course info)."""
    with open(DATA_DIR / "courses.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_bridges() -> dict:
    """Load bridge taxonomy (gap_skill -> {via, confidence})."""
    with open(DATA_DIR / "bridges.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_skill_taxonomy() -> dict:
    """Load skill taxonomy grouped by sector."""
    with open(DATA_DIR / "skill_taxonomy.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_skill_registry() -> dict:
    """Load the SWDA-derived skill registry.

    Maps each skill title to its metadata: ``type`` (tsc/ccs), ``description``,
    ``category``, ``sectors`` (SkillBridge ids), ``emerging``/``casl`` flags and
    per-level ``proficiency_descriptions`` (keys "1".."6").
    """
    with open(DATA_DIR / "skill_registry.json", encoding="utf-8") as f:
        return json.load(f)


def get_all_skills() -> set[str]:
    """Return a flat set of all known skills across all sectors."""
    taxonomy = get_skill_taxonomy()
    skills: set[str] = set()
    for sector_skills in taxonomy.values():
        skills.update(sector_skills)
    return skills


# Curated What-If explorer skills — real, recognizable SWDA skills that
# differentiate the candidate pool (a mix of in-demand technical and
# cross-sector transferable skills). They are validated against the live
# taxonomy at render time so a renamed/removed skill can never silently
# render a dead checkbox that has no effect on match scores.
WHATIF_SKILLS = [
    "Artificial Intelligence Application",
    "Data Analytics",
    "Project Management",
    "Cyber Risk Management",
    "Stakeholder Management",
    "Data Governance",
]


def get_whatif_skills() -> list[str]:
    """Return the curated What-If skills that exist in the live taxonomy."""
    known = get_all_skills()
    return [skill for skill in WHATIF_SKILLS if skill in known]
