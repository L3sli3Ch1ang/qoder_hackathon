"""Seed data validation for SkillBridge.

Run as a module::

    python -m app.validate_seed_data

Enforces the Phase 2 data-quality gate:
  * expected record counts (150 candidates / 30 jobs),
  * required fields and types on every record,
  * course and bridge mapping structure,
  * the 5-sector taxonomy,
  * detection of duplicate ``bridges.json`` keys (which ``json.load``
    silently collapses) via ``object_pairs_hook``.

Exits 0 when all checks pass, 1 otherwise.
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

EXPECTED_CANDIDATES = 150
EXPECTED_JOBS = 30
EXPECTED_SECTORS = {"finance", "ict", "healthcare", "engineering", "sustainability"}

CANDIDATE_FIELDS = {
    "id": str,
    "name": str,
    "sector": str,
    "title": str,
    "years_experience": int,
    "skills": list,
    "skill_levels": dict,
    "certifications": list,
    "summary": str,
}

JOB_FIELDS = {
    "id": str,
    "title": str,
    "sector": str,
    "skills_required": list,
    "skill_requirements": dict,
    "description": str,
}

COURSE_FIELDS = {"course_name": str, "provider": str, "url": str, "duration_hours": int}

BRIDGE_FIELDS = {"via": str, "confidence": (int, float)}


def _load(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _check_fields(record: dict, fields: dict, label: str, errors: list[str]) -> None:
    for field, expected in fields.items():
        if field not in record:
            errors.append(f"{label}: missing field '{field}'")
        elif not isinstance(record[field], expected):
            errors.append(
                f"{label}: field '{field}' should be {expected}, "
                f"got {type(record[field]).__name__}"
            )


def validate_candidates(errors: list[str]) -> None:
    candidates = _load("candidates.json")
    if len(candidates) != EXPECTED_CANDIDATES:
        errors.append(
            f"candidates.json: expected {EXPECTED_CANDIDATES} records, got {len(candidates)}"
        )
    seen_ids = set()
    for i, cand in enumerate(candidates):
        label = f"candidates[{i}] ({cand.get('id', '?')})"
        _check_fields(cand, CANDIDATE_FIELDS, label, errors)
        if cand.get("sector") and cand["sector"] not in EXPECTED_SECTORS:
            errors.append(f"{label}: unknown sector '{cand['sector']}'")
        cid = cand.get("id")
        if cid in seen_ids:
            errors.append(f"{label}: duplicate candidate id '{cid}'")
        seen_ids.add(cid)
        levels = cand.get("skill_levels")
        if isinstance(levels, dict):
            if set(cand.get("skills", [])) != set(levels.keys()):
                errors.append(f"{label}: 'skills' must equal the keys of 'skill_levels'")
            for sk, pl in levels.items():
                if isinstance(pl, bool) or not isinstance(pl, int) or not (1 <= pl <= 6):
                    errors.append(f"{label}: skill_levels['{sk}'] proficiency {pl!r} not an int in 1-6")


def validate_jobs(errors: list[str]) -> None:
    jobs = _load("jobs.json")
    if len(jobs) != EXPECTED_JOBS:
        errors.append(f"jobs.json: expected {EXPECTED_JOBS} records, got {len(jobs)}")
    seen_ids = set()
    for i, job in enumerate(jobs):
        label = f"jobs[{i}] ({job.get('id', '?')})"
        _check_fields(job, JOB_FIELDS, label, errors)
        if job.get("sector") and job["sector"] not in EXPECTED_SECTORS:
            errors.append(f"{label}: unknown sector '{job['sector']}'")
        jid = job.get("id")
        if jid in seen_ids:
            errors.append(f"{label}: duplicate job id '{jid}'")
        seen_ids.add(jid)
        reqs = job.get("skill_requirements")
        if isinstance(reqs, dict):
            if set(job.get("skills_required", [])) != set(reqs.keys()):
                errors.append(f"{label}: 'skills_required' must equal the keys of 'skill_requirements'")
            for sk, pl in reqs.items():
                if isinstance(pl, bool) or not isinstance(pl, int) or not (1 <= pl <= 6):
                    errors.append(f"{label}: skill_requirements['{sk}'] proficiency {pl!r} not an int in 1-6")


def validate_courses(errors: list[str]) -> None:
    courses = _load("courses.json")
    if not isinstance(courses, dict) or not courses:
        errors.append("courses.json: expected a non-empty object")
        return
    for skill, course in courses.items():
        label = f"courses['{skill}']"
        if not isinstance(course, dict):
            errors.append(f"{label}: expected an object")
            continue
        _check_fields(course, COURSE_FIELDS, label, errors)


def validate_bridges(errors: list[str]) -> None:
    # Detect duplicate keys, which json.load silently collapses to last-wins.
    duplicates: list[str] = []

    def pairs_hook(pairs):
        keys = [k for k, _ in pairs]
        for key in keys:
            if keys.count(key) > 1 and key not in duplicates:
                duplicates.append(key)
        return dict(pairs)

    with open(DATA_DIR / "bridges.json", encoding="utf-8") as f:
        bridges = json.load(f, object_pairs_hook=pairs_hook)

    for key in duplicates:
        errors.append(f"bridges.json: duplicate key '{key}' (JSON collapses duplicates)")

    if not isinstance(bridges, dict) or not bridges:
        errors.append("bridges.json: expected a non-empty object")
        return
    for gap_skill, bridge in bridges.items():
        label = f"bridges['{gap_skill}']"
        if not isinstance(bridge, dict):
            errors.append(f"{label}: expected an object")
            continue
        _check_fields(bridge, BRIDGE_FIELDS, label, errors)
        conf = bridge.get("confidence")
        if isinstance(conf, (int, float)) and not (0.0 <= conf <= 1.0):
            errors.append(f"{label}: confidence {conf} outside [0, 1]")


def validate_skill_registry(errors: list[str]) -> None:
    registry = _load("skill_registry.json")
    if not isinstance(registry, dict) or not registry:
        errors.append("skill_registry.json: expected a non-empty object")
        return
    for skill, meta in registry.items():
        label = f"skill_registry['{skill}']"
        if not isinstance(meta, dict):
            errors.append(f"{label}: expected an object")
            continue
        if meta.get("type") not in ("tsc", "ccs"):
            errors.append(f"{label}: type {meta.get('type')!r} not in {{tsc, ccs}}")
        if not isinstance(meta.get("sectors"), list):
            errors.append(f"{label}: 'sectors' must be a list")
        if not isinstance(meta.get("emerging"), bool):
            errors.append(f"{label}: 'emerging' must be a bool")
        if not isinstance(meta.get("casl"), bool):
            errors.append(f"{label}: 'casl' must be a bool")


def validate_cross_references(errors: list[str]) -> None:
    """Every skill referenced by candidates/jobs/bridges exists in the registry."""
    known = set(_load("skill_registry.json").keys())
    for cand in _load("candidates.json"):
        for sk in cand.get("skills", []):
            if sk not in known:
                errors.append(f"cross-ref: candidate skill '{sk}' not in skill_registry")
    for job in _load("jobs.json"):
        for sk in job.get("skills_required", []):
            if sk not in known:
                errors.append(f"cross-ref: job skill '{sk}' not in skill_registry")
    for gap, info in _load("bridges.json").items():
        if gap not in known:
            errors.append(f"cross-ref: bridge gap skill '{gap}' not in skill_registry")
        via = info.get("via") if isinstance(info, dict) else None
        if via and via not in known:
            errors.append(f"cross-ref: bridge via skill '{via}' not in skill_registry")


def validate_taxonomy(errors: list[str]) -> None:
    taxonomy = _load("skill_taxonomy.json")
    if not isinstance(taxonomy, dict):
        errors.append("skill_taxonomy.json: expected an object")
        return
    sectors = set(taxonomy.keys())
    if sectors != EXPECTED_SECTORS:
        errors.append(
            f"skill_taxonomy.json: sectors {sorted(sectors)} != expected {sorted(EXPECTED_SECTORS)}"
        )
    for sector, skills in taxonomy.items():
        if not isinstance(skills, list) or not skills:
            errors.append(f"skill_taxonomy['{sector}']: expected a non-empty list")


def main() -> int:
    errors: list[str] = []
    validators = (
        validate_candidates,
        validate_jobs,
        validate_courses,
        validate_bridges,
        validate_taxonomy,
        validate_skill_registry,
        validate_cross_references,
    )
    for validator in validators:
        try:
            validator(errors)
        except FileNotFoundError as exc:
            errors.append(f"{validator.__name__}: file not found ({exc})")
        except json.JSONDecodeError as exc:
            errors.append(f"{validator.__name__}: invalid JSON ({exc})")

    if errors:
        print(f"Seed data validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Seed data validation PASSED:")
    print(f"  - {EXPECTED_CANDIDATES} candidates, {EXPECTED_JOBS} jobs")
    print(f"  - courses + bridges structure OK, no duplicate bridge keys")
    print(f"  - taxonomy covers {len(EXPECTED_SECTORS)} sectors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
