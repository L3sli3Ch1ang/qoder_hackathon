# SkillBridge — Progress Log

> Running record of work toward the Alibaba Cloud × Qoder Hackathon Singapore 2026
> submission (deadline 5 Aug 2026). Newest entries at the bottom of each phase.
>
> **Entry format:** `Date · Phase · Objective → Work completed · Evidence · Status`

---

## Phase 1 — Specification & Scaffold

### 2026-07-29 · Phase 1 · Project specification
- **Objective:** Lock the product scope, architecture, and acceptance gates.
- **Work completed:** Authored `spec.md` — SkillBridge defined as a skill-to-job matching
  engine across five Singapore sectors (Finance, Infocomm Technology (ICT), Healthcare, Engineering,
  Sustainability). Fixed the 8-stage hybrid retrieval pipeline (BM25 + dense → Reciprocal Rank Fusion (RRF) →
  cross-encoder rerank → explainability → surprise filter → Large Language Model (LLM) narrative → course mapper),
  the FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind front end, and the Section-10
  documentation/evidence requirements.
- **Evidence:** `spec.md` (attached to project brief); sector taxonomy seeded from
  SkillsFuture-aligned skill sets.
- **Status:** ✅ Done

### 2026-07-29 · Phase 1 · Repository scaffold
- **Objective:** Stand up a runnable FastAPI skeleton with config, data loaders, and CI-ready tests.
- **Work completed:** Created `app/main.py` (FastAPI app, `/health`, `/`), `app/config.py`
  (pydantic-settings with `SKILLBRIDGE_` env prefix), `app/data/__init__.py` (cached JSON
  loaders), empty pipeline module stubs, and `tests/test_scaffold.py`.
- **Evidence:** `tests/test_scaffold.py` — imports, config load, app start, `/health` == `{"status":"ok"}`.
- **Status:** ✅ Done (4 scaffold tests green)

---

## Phase 2 — Build the Matching Engine

### 2026-07-30 · Phase 2 (2a) · Lexical + semantic retrieval
- **Objective:** Hybrid candidate recall.
- **Work completed:** `bm25_search.py` (BM25Okapi over title/sector/skills/certs/summary,
  top-50) and `dense_search.py` (all-MiniLM-L6-v2 embeddings into Qdrant Lite, 384-dim,
  cosine, top-50; collection auto-indexes once and is reused on subsequent starts).
- **Evidence:** `tests/test_bm25.py` (5 tests); `tests/test_dense_search.py` (6 tests:
  384-dim vectors, `semantic_score` present + sorted desc, 150 points indexed, reuse-not-reindex).
- **Status:** ✅ Done

### 2026-07-30 · Phase 2 (2b) · Fusion + reranking
- **Objective:** Merge recall lists and re-rank with a cross-encoder.
- **Work completed:** `rrf_fusion.py` (Reciprocal Rank Fusion, k=60, dedup, top-30, both
  scores preserved) and `reranker.py` (cross-encoder/ms-marco-MiniLM-L-6-v2, top-10).
- **Evidence:** `tests/test_rrf.py` (4 tests: dedup, score preservation, top-K, sort order).
- **Status:** ✅ Done

### 2026-07-31 · Phase 2 (2c) · Explainability + surprise filter
- **Objective:** Make matches interpretable and add a serendipity mode.
- **Work completed:** `explainability.py` (taxonomy-grounded skill extraction, case-insensitive
  matched/gap split, bridge mapping via adjacent skills) and `surprise_filter.py`
  (re-sort by `semantic_score / (lexical_score + ε)`, flags `is_surprise`).
- **Evidence:** `tests/test_explainability.py` (5 tests) and `tests/test_surprise_filter.py` (4 tests).
- **Status:** ✅ Done

### 2026-07-31 · Phase 2 (2d) · Narrative generation + course mapping
- **Objective:** Human-readable explanations and upskilling paths.
- **Work completed:** `narrative.py` (DashScope / Alibaba Cloud Model Studio, `qwen-plus`,
  parallel `asyncio.gather`, with an offline template fallback when no API key / on failure)
  and `course_mapper.py` (skill → SkillsFuture Singapore (SSG) course, with a SkillsFuture directory fallback URL).
- **Evidence:** `tests/test_course_mapper.py` (7 tests incl. data-loader checks); fallback
  narrative exercised by the hermetic e2e suite (no API key).
- **Status:** ✅ Done

### 2026-08-01 · Phase 2 (2e) · Orchestration + Application Programming Interface (API) + User Interface (UI) wiring
- **Objective:** Coordinate all stages and expose them through the API and UI.
- **Work completed:** `orchestrator.py` (singleton coordinating stages 1–8, normalized
  40–98 display score), `app/api/routes.py` (`POST /api/match`, HTMX partial vs JSON),
  `app/api/schemas.py` (pydantic request/response models), and the four templates
  (`base.html`, `index.html`, `partials/results.html`, `partials/result_card.html`).
- **Evidence:** `tests/test_pipeline_e2e.py` (6 TestClient tests); manual browser run.
- **Status:** ✅ Done

### 2026-08-01 · Phase 2 · TemplateResponse signature fix
- **Objective:** Resolve the Starlette `TemplateResponse` deprecation/breakage.
- **Work completed:** Migrated all renders to the new `TemplateResponse(request, name, context)`
  signature (request first) across `app/main.py` and `app/api/routes.py`.
- **Evidence:** App boots and renders `/` and `/api/match` (HTMX) without warnings-as-errors.
- **Status:** ✅ Done

---

## Phase 2 — Polish & Theming

### 2026-08-02 · Phase 2 · Dark / light theme
- **Objective:** Deliver a polished, accessible dual-theme UI.
- **Work completed:** Token-based theming in `base.html` — every color resolves to a CSS custom
  property (`--paper`, `--ink`, `--brand`, sector lines, match/gap/bridge accents) with a `.dark`
  override block; theme toggle persists to `localStorage` (`sb-theme`) and is applied pre-paint to
  avoid a flash of the wrong theme.
- **Evidence:** User-verified in the browser — both themes render correctly (see
  `canvases/dark_mode.png` completion report).
- **Status:** ✅ Done (user-verified)

---

## Phase 2 — Verification & Gap Closure (this session)

### 2026-08-03 · Phase A · Verify Phase 2 against its testing gate
- **Objective:** Prove Phase 2 is complete and close the missing test/validator gaps.
- **Work completed:**
  - Ran baseline `pytest tests/ -v` → **30 passed**.
  - **Bug fix (High):** `orchestrator.py` surprise mode zipped the surprise-re-ordered
    `top_candidates` against the original-order `skills_list`, attaching the wrong candidate's
    matched/gap/bridge skills. Fixed by rebuilding `skills_list = [c["skills_analysis"] for c in
    top_candidates]` after the surprise filter (each candidate already carries its own analysis).
  - Added `tests/test_dense_search.py` (6 tests) and `tests/test_pipeline_e2e.py` (6 tests, incl.
    a regression test asserting `matched ⊆ candidate.skills` and `gap ∩ candidate.skills = ∅`
    for every surprise result — guards the fixed bug).
  - Added `app/validate_seed_data.py` (`python -m app.validate_seed_data`): enforces 150 candidates
    / 30 Job Descriptions (JDs), required fields/types, course + bridge structure, the 5-sector taxonomy, and detects
    duplicate `bridges.json` keys via `object_pairs_hook`; exits 0/1.
  - **Data fix (Med):** `bridges.json` had 20 duplicate keys that `json.load` silently collapses.
    De-duplicated to 31 unique entries, keeping the higher-confidence bridge for each key.
- **Evidence:** `pytest tests/ -v` → **42 passed, 1 warning**; `python -m app.validate_seed_data`
  → exit 0 ("150 candidates, 30 jobs … no duplicate bridge keys … 5 sectors").
- **Status:** ✅ Done

### 2026-08-03 · Phase B · Recruiter / candidate perspective toggle
- **Objective:** Implement the remaining spec "Should" feature used in the demo script.
- **Work completed:** Both framings render server-side and toggle client-side via a shared
  `Alpine.store('ui', { perspective })` for an instant, no-re-query switch.
  - `base.html`: registered the store on `alpine:init` (persisted to `localStorage` `sb-perspective`);
    added a segmented [Recruiter | Candidate] control in the header beside the theme toggle.
  - `index.html`: `sendMatch()` now includes `Alpine.store('ui').perspective` in the POST body.
  - `routes.py`: passes `perspective` into the `partials/results.html` context.
  - `result_card.html`: framing banner with two `x-show` variants — recruiter ("Hire readiness — N
    transferable skills verified; probe <top gap> in interview") and candidate ("Your upskill path —
    build on <top matched>; close <top gap> with the mapped courses").
- **Evidence:** In-process render via `TestClient` (real templates, offline narratives) →
  **13/13 checks passed**: the index page carries the `Alpine.store('ui')` registration, both
  [Recruiter | Candidate] buttons, `localStorage('sb-perspective')` persistence, and the theme
  toggle; the HTMX match partial renders BOTH framing banners keyed off
  `Alpine.store('ui').perspective`, guarded by `x-cloak`. This is the same Alpine-store + `x-show`
  + localStorage mechanism already user-verified for dark/light theme, so the toggle re-frames
  cards instantly in both themes.
- **Status:** ✅ Done (HTML-level verified). A live click-through could not be captured because a
  standalone uvicorn server could not be kept running this session (terminal intermittently
  unavailable); the toggle shares the user-verified theme-toggle mechanism.

### 2026-08-03 · Phase D · Documentation & evidence
- **Objective:** Satisfy spec Section 10 deliverables.
- **Work completed:** This `docs/evidence/` tree — `progress-log.md`, per-phase `notes.md`
  (with screenshot placeholder slots), four `code-reviews/*.md`, and root `AGENTS.md`.
- **Evidence:** Files under `docs/evidence/` and `AGENTS.md`.
- **Status:** ✅ Done

---

## Phase 5 — Edge cases (this session)

### 2026-08-03 · Phase C · Edge-case hardening
- **Objective:** Confirm graceful behaviour on degenerate inputs.
- **Work completed / verified (via the passing e2e suite):**
  - Empty input → `POST /api/match` with `jd_text=""` returns **HTTP 422** (pydantic `min_length=1`),
    never a 500 — `test_empty_jd_rejected_with_422`.
  - Very long JD (~5400 chars) → still returns 10 results, no error — `test_very_long_jd_returns_results`.
  - No matches → `partials/results.html` renders the "No matches found" empty state
    (`{% elif results|length == 0 %}` branch).
- **Latency (measured in-process via TestClient, CPU, offline narratives; n=3 ranked + 1 surprise):**
  ranked avg **336.8 ms** (min 295.1 / max 395.0; warm-up 352.2 ms), surprise **381.0 ms**.
  The cross-encoder rerank over the top-30 fused candidates dominates; BM25 + dense recall and the
  narrative fallback are comparatively cheap. Comfortably interactive for a live demo.
- **Status:** ✅ Done (edge cases + latency verified)

### 2026-08-03 · Final gate · Full suite re-confirmed after all edits
- **Objective:** Re-confirm the Phase 2 testing gate after the Phase B template/route changes.
- **Work completed:** Cleared the hung terminal (a `^C`-orphaned background server had been blocking
  all commands) and re-ran the gate **directly** — direnv's `use flake` pre-loads the cached dev shell
  (`VIRTUAL_ENV` + `LD_LIBRARY_PATH` exported), so no `nix develop` wrapper is needed.
- **Evidence:** `pytest tests/ -q` → **42 passed, 1 warning in 42.31s** (exit 0);
  `python -m app.validate_seed_data` → **PASSED** (150 candidates / 30 jobs, courses + bridges OK,
  no duplicate bridge keys, 5-sector taxonomy; exit 0).
- **Status:** ✅ Done — all gates green after every edit.

---

## Phase 3 — Command-Line Interface (CLI) Automation (user-side, prepared this session)

> The four `qodercli` actions below are spec Phase 3. The commands, expected outputs, and evidence
> paths are pre-written; the actual CLI runs + screenshots are performed by the user (full script in
> `docs/evidence/phase3-cli/notes.md`).

### 2026-08-03 · Phase 3 · CLI-driven test execution
- **Objective:** Demonstrate `qodercli` running the test suite.
- **Command:** `qodercli -p "run pytest tests/ -v and report failures"`
- **Expected:** 54 passed, 0 failures (unit + dense + e2e + surprise regression + sector convergence).
- **Evidence:** `docs/evidence/phase3-cli/screenshot_cli_tests.png` (to capture).
- **Status:** ⏳ Prepared — awaiting user CLI run + screenshot.

### 2026-08-03 · Phase 3 · Isolated worktree
- **Objective:** Demonstrate isolated branching via the CLI.
- **Command:** `qodercli --worktree feature-explainability`
- **Expected:** A new worktree/branch (`feature-explainability`) for the explainability engine.
- **Evidence:** `docs/evidence/phase3-cli/screenshot_cli_worktree.png` (to capture).
- **Status:** ⏳ Prepared — awaiting user CLI run + screenshot.

### 2026-08-03 · Phase 3 · `/review` on the Machine Learning (ML) pipeline
- **Objective:** Automated code review before merge; save the output.
- **Command:** `/review` (scope `app/pipeline/`) inside `qodercli`.
- **Expected:** Review findings; the High-severity surprise-alignment bug is already found + fixed +
  regression-tested (curated in `code-reviews/review_ml_pipeline.md`, verdict Approve).
- **Evidence:** `docs/evidence/phase3-cli/screenshot_cli_review.png` (to capture) +
  `docs/evidence/phase3-cli/cli_review_output.md` (raw paste template ready).
- **Status:** ⏳ Prepared — awaiting user CLI run + raw-output paste.

### 2026-08-03 · Phase 3 · `/init` → AGENTS.md
- **Objective:** Persist project knowledge via the CLI.
- **Command:** `/init` inside `qodercli`.
- **Expected:** `AGENTS.md` at repo root (architecture, config table, data/API contract, run/test
  commands, testing conventions, known pitfalls) — already present and refreshed this session
  (54 tests, SectorConvergence component, convergence strip + filters).
- **Evidence:** `AGENTS.md` + terminal showing `/init`.
- **Status:** ✅ `AGENTS.md` present; ⏳ user to run `/init` + screenshot.

---

## Phase 6 — Skills & Workforce Development Agency (SWDA) Data Enhancement (this session)

### 2026-07-29 · Phase 6 · Re-ground seed data in official SWDA Skills Framework
- **Objective:** Replace hand-crafted seed data with data derived from the official SWDA Skills
  Framework dataset; upgrade matching from binary skill-set comparison to proficiency-aware
  (candidate Proficiency Level (PL) vs required PL, 1–6); derive bridges from shared Knowledge & Ability (K&A) items; surface Emerging/Course Approval Skills List (CASL)
  signals.
- **Work completed:**
  - Downloaded + schema-verified 3 official SWDA workbooks (`.research/`; git-ignored).
  - Step 0: enumerated all 38 sectors, locked 5-sector mapping (finance→Financial Services,
    ict→Infocomm Technology, healthcare→Healthcare, engineering→Engineering Services,
    sustainability→Carbon Services and Trading + Environmental Services).
  - `scripts/xlsx_util.py` (stdlib Office Open XML (OOXML) reader) + `scripts/build_swda_seed.py` (deterministic
    generator, no pip). Regenerated all 6 seed JSON files from real data.
  - **New `app/data/skill_registry.json`** — 434 skills with type, description, category, sectors,
    Emerging/CASL flags (67 emerging, 82 CASL), per-level proficiency descriptions.
  - **`jobs.json`** — 30 real SWDA roles + `skill_requirements` (skill→PL) + `key_tasks`.
  - **`candidates.json`** — 150 candidates + `skill_levels` (skill→PL), anchored to real roles.
  - **`bridges.json`** — 53 evidence-based bridges (K&A containment, confidence 0.20–0.87).
  - **`courses.json`** — 434 entries keyed to real skill titles (grounded SSG-style placeholders).
  - Proficiency-aware `explainability.py` (`matched_detail`, `proficiency_fit ∈ [0,1]`).
  - `orchestrator.py`: required-level resolution (seeded-job match or seniority heuristic),
    60/40 hybrid score blend, Emerging/CASL surfacing.
  - `schemas.py`: additive `MatchResult` fields (`proficiency_fit`, `matched_detail`,
    `emerging_skills`, `casl_skills`).
  - `result_card.html`: PL-fit pill, Emerging/CASL badges, `L≥L` proficiency annotations.
  - `validate_seed_data.py`: proficiency-range, registry, cross-reference checks — **passes**.
  - `.gitignore` created (excludes `.research/`, caches, `qdrant_data/`).
- **Evidence:** `python -m app.validate_seed_data` → exit 0; `.research/step0_report.txt`;
  `.research/build_report.txt`; `docs/evidence/phase6-swda-enhancement/spec.md` (full record copy).
- **Status:** ✅ Done — all 12 workstreams complete; `pytest` → 71 passed; validator → exit 0.

---

## Phase 7 — What-if Skill Explorer fix (this session)

### 2026-08-02 · Phase 7 · Make the What-if explorer actually shift match scores
- **Objective:** Fix the "Experiment 3 — What-if skill explorer" so toggling a skill visibly
  changes the match scores (user report: "the match score does not seem to shift").
- **Root causes found (3 distinct bugs):**
  1. **Fake skills in the checkbox list** — 4 of the 6 hard-coded What-if skills were not in the
     live SWDA taxonomy, so `extract_skills()` (substring match against the taxonomy) never saw
     them and they had zero effect on any score.
  2. **Added skills dropped from the proficiency fit** — when the pasted Job Description (JD) named a seeded role,
     `_resolve_required_levels()` only returned required levels for the seeded role's own
     requirements; a What-if-added skill not in that set got `req_pl=None` and was silently
     excluded from `proficiency_fit`, so it could not move the blended score.
  3. **Loose job-title matching** — the seeded-role lookup used a plain substring match, so a JD
     for "Senior Data Engineer" matched the generic "Engineer" role and inherited the wrong
     requirements.
- **Work completed:**
  - `app/data/__init__.py`: `WHATIF_SKILLS` — 6 real, recognizable SWDA skills, validated against
    the live taxonomy via `get_whatif_skills()` so a dead checkbox can never render again.
  - `app/pipeline/orchestrator.py`: rewrote `_resolve_required_levels()` as an overlay (seniority
    baseline for every JD skill, then seeded-role requirements on top — added skills are never
    dropped) and added `_match_seeded_job()` (word-boundary title match, skips single-word titles).
  - `templates/index.html` + `partials/result_card.html`: What-if checkboxes render dynamically;
    toggling a skill auto-reruns the match (400 ms debounce) and each card shows a score-delta
    badge (▲ +N rise / ▼ −N fall / NEW) versus the previous run.
- **Evidence:** `tests/test_whatif_shift.py` (7 regression tests, incl. a Bug #2 regression that
  asserts an added skill shifts `proficiency_fit` for a JD naming a seeded role); full suite
  `pytest -q` → **97 passed**; live browser verification — toggling "Data Analytics" on the
  "IoT Data Engineer" JD shifted 8 scores (▲ +5 top riser) and surfaced 2 new candidates with
  delta badges rendered.
- **Status:** ✅ Done — What-if explorer verified working end-to-end (API + UI).

---

## Outstanding / user-side
- Actual Qoder desktop screenshots (placeholder slots provided in each `notes.md`).
- `qodercli` CLI runs — **Phase 3 fully prepped** (`notes.md` script, `cli_review_output.md` paste
  template, `AGENTS.md` ready); only the live runs + screenshots + log fill-in remain. Plus Quest
  Knowledge hub cards and the social post.
- Demo video — `demo-video/` composition refreshed for the current UI (Hire ↔ Upskill naming,
  dedicated What-if scene with live-captured delta badges, 97-test count) and re-rendered to
  `demo-video/output.mp4` (180 s); upload to a shareable link for the submission form + social post.
- ✅ Live click-through of the perspective toggle and the What-if explorer — completed this session
  (browser-verified: Upskill reframing + What-if score deltas with ▲/▼/NEW badges).
