# Changelog

Notable changes to SkillBridge. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## 2026-08-03

### Added
- **README.md** — comprehensive reference documentation: mission & objectives,
  the 8-stage matching engine (exact models, parameters, and scoring formula),
  data provenance (how JDs / candidates / bridges / courses are derived from the
  official SWDA dataset — deterministic, not AI-hallucinated), the full feature
  list, explicit can / cannot boundaries, and a roadmap for future investment.
- **What-if skill explorer UX.** Detected JD skills render **checked by default**
  (every skill is folded into the match) with a **Clear all** button, so a
  recruiter can either uncheck the one or two skills they don't need, or clear
  everything and pick just the one or two to prioritise. A curated,
  taxonomy-validated skill list (`get_whatif_skills`) guarantees no dead
  checkboxes (`templates/index.html`, `app/data/__init__.py`).
- **Candidate full-profile endpoint + modal** — `GET /candidate/{id}` returns the
  complete CV (skills, proficiency levels, certifications, summary) so a recruiter
  can verify the narrative's claims against the actual profile
  (`app/api/routes.py`, `app/api/schemas.py`).
- **Demo video re-cut to 15 scenes (180 s)** — added a dedicated **Matching Engine**
  deep-dive (BM25 → dense → RRF k=60 → cross-encoder → proficiency fit → 0.3/0.7
  hybrid score → explainability → courses) and a **Data Provenance** scene,
  bookended by a mission statement (`demo-video/index.html`, `demo-video/output.mp4`).

### Changed
- **Hybrid display score now weights skill match at 70%** — was 60% semantic /
  40% proficiency fit, now 30% / 70% so a real skill match dominates and text
  similarity alone cannot inflate a score. Ranked results are additionally
  re-sorted by the blended score so the displayed order follows the skill match
  (`app/pipeline/orchestrator.py`).
- **Required-level resolution guarantees every extracted JD skill a proficiency
  level** (seniority baseline overlaid with the matched SWDA role's authoritative
  requirements), so What-if additions always influence the fit — previously a
  matched job's requirements silently dropped the other skills. Seeded-job title
  matching now uses word boundaries and ignores single-word generic titles
  (`app/pipeline/orchestrator.py`).
- **Anti-hallucination narratives** — the DashScope prompt is grounded in the
  explainability output ("reference only these skills, do not invent others"), and
  the offline fallback cites the candidate's real profile skills
  (`app/pipeline/narrative.py`).

### Performance
- **Faster result load** — when no DashScope API key is configured the narrative
  stage short-circuits straight to the offline template instead of issuing a batch
  of instantly-failing HTTP calls on every match (`app/pipeline/narrative.py`).

### Fixed
- `spec.md` / `spec-video.md` — corrected the documented blend weights to the
  actual 0.3 / 0.7, refreshed the video breakdown to the 15-scene cut, and added a
  prominent mission statement for the judges.

### Tests
- Suite expanded to **97 tests** (new coverage for what-if score shifts, the
  candidate endpoint, sample JDs, narratives, and summaries).

## 2026-07-31

### Fixed
- **What-If skill removal is now case-insensitive and taxonomy-aware.**
  `removed_skills` previously used exact-case `str.replace`, so removing
  "Data Governance" left "data governance" in the JD text; it could also clip
  a longer, distinct skill title (removing "Change Management" destroyed
  "Climate Change Management"). Removal now mirrors `extract_skills`
  (case-insensitive), preserves standalone occurrences inside longer taxonomy
  skill titles, and explicitly drops removed skills from the extracted JD
  skill set (`app/pipeline/orchestrator.py`).
- **Narrative score now matches the displayed score.** The DashScope prompt
  computed its own "% match" from the raw cross-encoder score with a broken
  heuristic (a strong raw score of 8.7 became "40%"), so the narrative could
  quote a different percentage than the result card. The blended display
  score (60% semantic + 40% proficiency fit) is now computed once in the
  orchestrator — after any surprise re-ordering — and passed to the narrative
  generator (`app/pipeline/narrative.py`, `app/pipeline/orchestrator.py`).

### Added
- `tests/test_whatif_removal.py` — 5 data-driven unit tests for What-If skill
  removal (case-insensitivity, longer-title preservation, mid-word safety,
  regex escaping).
- `tests/test_narrative_score_e2e.py` — hermetic integration test driving the
  full `/api/match` pipeline with a stubbed DashScope client, asserting the
  narrative's "% match" equals the displayed `score` in both `ranked` and
  `surprise` modes. Suite total: 71 tests.

### Changed
- AGENTS.md trimmed to the minimal agent-guidance format (removed the
  file-by-file layout and documentation map; added the standard prefix).
- `app/pipeline/narrative.py` now reuses a single `httpx.AsyncClient` across
  the batch of narrative calls instead of creating one per candidate.

### Fixed (cleanup)
- Removed dead `jd_set` variable in `app/pipeline/explainability.py`.
- Corrected `_extract_jd_title` docstring to match the 80-char truncation
  behavior in `app/pipeline/orchestrator.py`.

## 2026-07-29

### Added
- Initial hackathon build: 8-stage matching pipeline (BM25 → dense →
  RRF → cross-encoder → explainability → surprise → narrative → courses),
  SWDA-grounded seed data, FastAPI + Jinja2/Alpine.js UI, 64 tests.
