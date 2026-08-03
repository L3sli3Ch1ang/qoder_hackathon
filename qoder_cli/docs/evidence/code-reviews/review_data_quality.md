# Code Review — Data Quality

**Scope:** `app/data/` — `candidates.json`, `jobs.json`, `courses.json`, `bridges.json`,
`skill_taxonomy.json`; plus the validator `app/validate_seed_data.py`.

## Summary
The seed corpus is realistic, internally consistent, and grounded in a five-sector SkillsFuture-aligned
taxonomy. A validator now enforces counts, schema, and structural integrity as a repeatable gate.

## Strengths
- **Realistic profiles.** 150 candidates carry plausible Singapore-context names, sector-appropriate
  titles, `years_experience`, skill lists, certifications (CPA/CFA/ACAMS/CISSP/FRM…), and detailed
  summaries with concrete achievements.
- **Taxonomy-grounded skills.** `skill_taxonomy.json` defines five coherent sectors
  (finance, ict, healthcare, engineering, sustainability); candidate/JD skills and the explainability
  engine all draw from this controlled vocabulary, keeping matched/gap analysis meaningful.
- **Plausible bridges & courses.** `bridges.json` maps gap skills to adjacent "via" skills with
  confidence scores; `courses.json` maps skills to SSG-style courses with provider/URL/duration/cost.
- **Repeatable validation gate.** `validate_seed_data.py` (`python -m app.validate_seed_data`)
  enforces 150 candidates / 30 JDs, required fields + types, course/bridge structure, the 5-sector
  taxonomy, confidence ∈ [0,1], unique ids, and duplicate-key detection — exiting 0/1 for CI.

## Findings
| # | Severity | File | Finding | Resolution |
|---|----------|------|---------|------------|
| 1 | **Med** | `bridges.json` | 20 keys were duplicated (e.g. `Machine Learning`, `Python`, `IoT`, `NLP`, `Zero Trust`). JSON objects cannot hold duplicate keys — `json.load` silently collapses them to the *last* occurrence, dropping the intended alternative bridges. | **Fixed** — de-duplicated to 31 unique keys, keeping the higher-confidence entry for each. `validate_seed_data.py` now detects duplicates via `object_pairs_hook` and fails the gate if any reappear. |
| 2 | Low | `candidates.json` | Some sector skill lists in the taxonomy repeat a skill within a sector (e.g. `Internal Controls` in finance). | Harmless (loaded into a set); could be tidied. |

## Verification
- `python -m app.validate_seed_data` → exit 0:
  `150 candidates, 30 jobs · courses + bridges structure OK, no duplicate bridge keys · 5 sectors`.
- `tests/test_course_mapper.py` data-loader tests confirm candidates/jobs/courses/bridges load.

## Recommendations
- Keep `validate_seed_data.py` in CI so future data edits can't reintroduce duplicate keys or schema drift.
- If alternative bridges are desired (multiple "via" options per gap), change the schema to
  `gap_skill -> [{via, confidence}, …]` rather than relying on duplicate keys.

## Verdict
✅ **Approve.** Profiles, taxonomy, bridges, and courses are realistic and consistent; the duplicate-key
defect is fixed and now guarded by the validator.
