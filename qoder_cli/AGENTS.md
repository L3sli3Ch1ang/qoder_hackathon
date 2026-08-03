# AGENTS.md

This file provides guidance to the AI agent when working with code in this repository.

SkillBridge is a skill-to-job matching demo for the Alibaba Cloud × Qoder Hackathon
Singapore 2026. FastAPI + Jinja2 + HTMX-style `fetch` + Alpine.js + Tailwind (Content Delivery Network (CDN)),
single process, embedded Qdrant Lite vector store. Targets NixOS; uses Alibaba Cloud
Model Studio (DashScope) for narratives with an offline template fallback.

## Architecture

```
POST /api/match  →  PipelineOrchestrator (singleton)
  1. BM25Search            lexical recall, top-50      (rank_bm25)
  2. DenseSearch           semantic recall, top-50     (all-MiniLM-L6-v2 → Qdrant Lite, 384-dim, cosine)
  3. RRFFusion             merge + dedup, top-30       (Reciprocal Rank Fusion (RRF), k=60)
  4. CrossEncoderReranker  re-rank, top-10             (cross-encoder/ms-marco-MiniLM-L-6-v2)
  5. ExplainabilityEngine  matched / gap / bridge + proficiency fit (taxonomy-grounded; Proficiency Level (PL) 1–6)
  6. SurpriseFilter        serendipity re-sort         (mode="surprise"; semantic/(lexical+ε))
  7. NarrativeGenerator    2-sentence explanation      (DashScope qwen-plus, parallel; offline fallback)
  8. CourseMapper          gap skill → SkillsFuture Singapore (SSG) course      (SkillsFuture-aligned; directory fallback URL)
```

The landing page precomputes pairwise sector skill overlap (`SectorConvergence`, Jaccard
over `skill_taxonomy.json`) once at startup in `main.py` — it is **not** part of the
per-request match flow.

### Layout
```
app/
  main.py                 FastAPI app, lifespan (builds orchestrator), /health, /
  config.py               Settings (pydantic-settings, env_prefix="SKILLBRIDGE_")
  validate_seed_data.py   data-quality gate (python -m app.validate_seed_data)
  api/routes.py           POST /api/match (HTMX partial vs JSON), error handling
  api/schemas.py          MatchRequest / MatchResponse / MatchResult / CourseInfo / BridgeInfo
  data/__init__.py        lru_cache JSON loaders (candidates/jobs/courses/bridges/taxonomy/registry)
  data/*.json             seed corpus (see Data)
  pipeline/*.py           the 8 stages + orchestrator + sector_convergence (precomputed Jaccard)
scripts/
  xlsx_util.py            dependency-free Office Open XML (OOXML) reader (stdlib zipfile + ElementTree)
  build_swda_seed.py      one-off generator: derives all 6 seed JSONs from Skills & Workforce Development Agency (SWDA) workbooks
  step0_explore.py        sector enumeration / sampling (Step-0 verification)
templates/
  base.html               shell, token-based light/dark theme, header controls (theme + perspective)
  index.html              input panel, filters, convergence strip, what-if explorer, results pane, sendMatch()
  partials/results.html   empty / error / list states
  partials/result_card.html  per-result card incl. perspective framing banner
tests/                    pytest suite (97 tests: unit + dense + e2e + surprise regression + sector convergence + registry + what-if removal + what-if shift + narrative score)
docs/evidence/            progress log, per-phase notes, code reviews
```

## Models & configuration
All settings are in `app/config.py`, overridable via environment variables prefixed `SKILLBRIDGE_`:

| Setting | Default | Env var |
|---|---|---|
| `MODEL_EMBEDDING` | `sentence-transformers/all-MiniLM-L6-v2` | `SKILLBRIDGE_MODEL_EMBEDDING` |
| `MODEL_RERANKER` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `SKILLBRIDGE_MODEL_RERANKER` |
| `QDRANT_PATH` | `./qdrant_data` | `SKILLBRIDGE_QDRANT_PATH` |
| `SEED_DATA_PATH` | `./app/data` | `SKILLBRIDGE_SEED_DATA_PATH` |
| `DASHSCOPE_API_KEY` | `""` (empty → offline fallback) | `SKILLBRIDGE_DASHSCOPE_API_KEY` |
| `DASHSCOPE_MODEL` | `qwen-plus` | `SKILLBRIDGE_DASHSCOPE_MODEL` |
| `DASHSCOPE_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `SKILLBRIDGE_DASHSCOPE_BASE_URL` |
| `BM25_TOP_K` / `DENSE_TOP_K` / `RRF_TOP_K` / `RERANK_TOP_K` / `RRF_K` | 50 / 50 / 30 / 10 / 60 | `SKILLBRIDGE_*` |

**DashScope-intl note:** for the Alibaba Cloud *international* endpoint, set
`SKILLBRIDGE_DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1` and an intl API key.
With no key set, narratives use the offline template fallback (the app still works end-to-end).

## Data
All seed data is **derived from the official SWDA Skills Framework dataset** (via `scripts/build_swda_seed.py`):
- `candidates.json` — 150 profiles: `{id, name, sector, title, years_experience, skills[], skill_levels{skill:PL}, certifications[], summary}`.
- `jobs.json` — 30 real SWDA roles: `{id, title, sector, skills_required[], skill_requirements{skill:PL}, key_tasks[], description}`.
- `courses.json` — 434 entries: `skill → {course_name, provider, url, duration_hours}` (grounded SSG-style; MySkillsFuture directory URLs).
- `bridges.json` — 53 entries: `gap_skill → {via, confidence}` (Knowledge & Ability (K&A)-containment-derived; confidence ∈ [0.2,0.87]).
- `skill_taxonomy.json` — 5 sectors: `finance, ict, healthcare, engineering, sustainability` (real Technical Skills & Competencies (TSC) / Critical Core Skills (CCS) titles).
- `skill_registry.json` — 434 skills: `{type, description, category, sectors[], emerging, casl, proficiency_descriptions{1..6}}`.

**Data sources:** official SWDA Skills Framework dataset (`skills_framework_dataset.xlsx`, 13 MB;
`unique_skills_list.xlsx`; `tsc_unique_mapping.xlsx`). Source workbooks are git-ignored in `.research/`.
To regenerate: place workbooks in `.research/` and run `python scripts/build_swda_seed.py` (stdlib only, deterministic).

**Proficiency scale (1–6, Bloom-like):** 1 Use → 2 Operate → 3 Apply → 4 Implement → 5 Analyse → 6 Assess/Lead.
CCS textual levels normalized: Foundation→1, Basic→2, Intermediate→3, Advanced→5.

**Data integrity:** JSON object keys must be unique — `json.load` silently collapses duplicates.
`validate_seed_data.py` detects this via `object_pairs_hook` and also validates proficiency ranges,
registry structure, and cross-file skill references. Keep the validator green.

## Application Programming Interface (API) contract
`POST /api/match`
```jsonc
// request
{ "jd_text": "string (min_length=1, required)",
  "mode": "ranked" | "surprise",          // default "ranked"
  "perspective": "recruiter" | "candidate", // default "recruiter"
  "added_skills": ["..."], "removed_skills": ["..."] }

// response (JSON when no HX-Request header)
{ "results": [ { "candidate_id", "name", "title", "sector", "years_experience",
                 "score" (int 40–98), "narrative", "matched": [], "gap": [],
                 "bridge": [{gap_skill, via_skill, confidence}],
                 "courses": [{skill, course_name, provider, url, duration_hours}],
                 "is_surprise",
                 "proficiency_fit" (float 0–1 | null),
                 "matched_detail": [{skill, required_pl, candidate_pl, met}],
                 "emerging_skills": [], "casl_skills": [] } ],
  "mode": "...", "total": 10 }
```
With header `HX-Request: true`, the same route returns the rendered `partials/results.html` HTML.
Empty `jd_text` → HTTP 422 (pydantic), never a 500.

Other endpoints: `GET /health` → `{"status":"ok"}`; `GET /` → the app page.

## Run & test commands
```bash
nix develop                         # enter the dev shell (Python 3.13, uv, qoder-cli; sets LD_LIBRARY_PATH)
uv pip install -r requirements.txt  # if the venv needs deps
uvicorn app.main:app --host 127.0.0.1 --port 8000   # serve (first start indexes Qdrant)

pytest tests/ -v                    # full suite (97 tests: unit + dense + e2e + surprise regression + sector convergence + registry + what-if removal + what-if shift + narrative score)
python -m app.validate_seed_data    # data-quality gate; exits 0 on success
```

## Testing conventions (important for agents)
- **Qdrant Lite holds a per-directory file lock** — only one process can open a `QDRANT_PATH`.
  Tests that build a `DenseSearch`/orchestrator **must** point `settings.QDRANT_PATH` at a fresh
  temp dir (see `tests/test_dense_search.py`, `tests/test_pipeline_e2e.py`) so they never fight the
  dev server's `./qdrant_data` lock.
- **Force offline narratives** in tests by setting `settings.DASHSCOPE_API_KEY = ""` (no network).
- **Reset the singleton** (`PipelineOrchestrator._instance = None`) before rebuilding the orchestrator
  with different settings; restore it on teardown.
- Use **module-scoped fixtures** to load models / index once per test module (model load is slow).

## Known pitfalls
- `TemplateResponse` must use the new `(request, name, context)` signature (already migrated).
- Duplicate JSON keys collapse silently — guard with `object_pairs_hook` (validator does this).
- Surprise mode must rebuild `skills_list` from each candidate's own `skills_analysis` *after* the
  surprise re-order, or skills detach from their candidate (fixed + regression-tested).
- NixOS: pip binary wheels (numpy/torch) need `LD_LIBRARY_PATH` to libstdc++/libgomp — handled by
  `flake.nix` (`nativeLibs`). Don't remove that.
- The venv has **no pip** — all new code must use stdlib or already-installed deps only.
- `skills` must stay a `list[str]` on candidates/jobs (BM25, dense search, and templates consume it);
  proficiency is in the parallel `skill_levels`/`skill_requirements` dicts.
- Seed data is SWDA-derived: old generic skill names (`Python`, `Kubernetes`, `Excel`) are NOT in the
  taxonomy. Tests must be data-driven (pick real skills from the registry/bridges/courses).

## Documentation map
- `docs/evidence/progress-log.md` — chronological work record.
- `docs/evidence/phase{1..4}-*/notes.md` — per-phase notes + screenshot slots.
- `docs/evidence/phase6-swda-enhancement/spec.md` — SWDA enhancement spec (annotated record copy).
- `docs/evidence/code-reviews/review_{ml_pipeline,backend,frontend,data_quality}.md` — reviews.
- `docs/research/swda-jobs-and-skills-research.md` — SWDA portal research (downloads, tools, 38 sectors).
