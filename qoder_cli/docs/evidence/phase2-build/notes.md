# Phase 2 — Build · Notes

**Goal:** Implement and verify the full matching engine, API, and UI.

## What was produced
- **Pipeline (`app/pipeline/`):** `bm25_search.py`, `dense_search.py`, `rrf_fusion.py`,
  `reranker.py`, `explainability.py`, `surprise_filter.py`, `narrative.py`, `course_mapper.py`,
  `orchestrator.py` (singleton coordinating stages 1–8).
- **API (`app/api/`):** `routes.py` (`POST /api/match` — HTMX partial vs JSON), `schemas.py`
  (pydantic `MatchRequest` / `MatchResponse` / `MatchResult`).
- **Templates (`templates/`):** `base.html` (theming + header controls), `index.html`
  (input panel, what-if explorer, results pane), `partials/results.html`, `partials/result_card.html`.
- **Seed data (`app/data/`):** 150 candidates, 30 JDs, 40 courses, 31 bridges, 5-sector taxonomy.

## Steps (2a–2e)
- **2a Retrieval:** BM25 top-50 + dense top-50 (MiniLM 384-dim → Qdrant Lite, cosine).
- **2b Fusion + rerank:** RRF (k=60) top-30 → cross-encoder (ms-marco-MiniLM-L-6-v2) top-10.
- **2c Explainability + surprise:** taxonomy-grounded matched/gap/bridge; serendipity re-sort.
- **2d Narrative + courses:** DashScope `qwen-plus` (parallel) with offline fallback; SSG course map.
- **2e Orchestration + API + UI:** singleton orchestrator, RESTful endpoint, Jinja UI wiring.

## Verification (this session)
- `pytest tests/ -v` → **42 passed** (unit + dense + e2e + surprise-skills regression).
- `python -m app.validate_seed_data` → exit 0.
- Dark/light theme user-verified in browser.

## Bugs found & fixed during verification
- **High — surprise skills misalignment** (`orchestrator.py`): rebuilt `skills_list` from each
  candidate's own `skills_analysis` after the surprise re-order. Regression-tested in
  `tests/test_pipeline_e2e.py::test_surprise_skills_align_to_correct_candidate`.
- **Med — duplicate bridge keys** (`bridges.json`): 20 duplicate keys collapsed by `json.load`;
  de-duplicated to 31 unique entries (kept higher confidence). Detected by `validate_seed_data.py`.

## Screenshot evidence (to be filled by user)
- [ ] _Screenshot: pipeline run / ranked results in browser_ — `docs/evidence/phase2-build/screenshots/ranked_results.png`
- [ ] _Screenshot: surprise mode results_ — `docs/evidence/phase2-build/screenshots/surprise_results.png`
- [ ] _Screenshot: pytest 42 passed_ — `docs/evidence/phase2-build/screenshots/pytest_full_suite.png`
- [ ] _Screenshot: dark mode_ — `docs/evidence/phase2-build/screenshots/dark_mode.png`
- [ ] _Screenshot: light mode_ — `docs/evidence/phase2-build/screenshots/light_mode.png`
- [ ] _Screenshot: perspective toggle (recruiter vs candidate)_ — `docs/evidence/phase2-build/screenshots/perspective_toggle.png`
