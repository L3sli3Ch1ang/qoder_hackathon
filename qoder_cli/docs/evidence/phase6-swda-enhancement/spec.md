# SkillBridge — SWDA Data Enhancement · Spec (updated record copy)

> **Provenance.** This is the record copy of the enhancement spec originally authored as the
> plan file `SkillBridge_SWDA_Data_Enhancement` (approved by the user). It is reproduced here
> with **live status annotations** plus a **progress review** and a **technical reference**
> ("necessary information") section, per the request to update the spec for what is done so far
> and keep a copy on record.
>
> **Date of this update:** 2026-07-29 · **Phase:** 6 — SWDA Data Enhancement
> **Overall status:** ✅ **All 12 workstreams complete.** Both gates pass:
> `python -m app.validate_seed_data` → exit 0; `pytest tests/ -q` → **64 passed** (44.9 s).

---

## 0. Status at a glance

| # | Workstream | Status |
|---|------------|--------|
| 1 | Step 0 — enumerate 38 sectors, lock 5-sector mapping, sample data | ✅ Done |
| 2 | `scripts/xlsx_util.py` + `scripts/build_swda_seed.py` generator (stdlib only) | ✅ Done |
| 3 | Regenerate 6 seed JSON files from the real SWDA workbooks | ✅ Done |
| 4 | `get_skill_registry()` loader | ✅ Done |
| 5 | Proficiency-aware `explainability.py` (`matched_detail`, `proficiency_fit`) | ✅ Done |
| 6 | Orchestrator: level resolution + hybrid score blend + new result fields | ✅ Done |
| 7 | `schemas.py` additive fields | ✅ Done |
| 8 | `result_card.html`: PL-fit pill, Emerging/CASL badges, PL annotations | ✅ Done |
| 9 | `validate_seed_data.py`: proficiency + registry + cross-reference checks | ✅ Done (passes) |
| 10 | Update data-dependent tests + new `test_skill_registry.py` | ✅ Done |
| 11 | `.gitignore` for `.research/` | ✅ Done |
| 12 | Full `pytest` green run after code changes | ✅ Done (64 passed) |

---

## Part A — Original spec (annotated)

### Summary
Replace SkillBridge's hand-crafted seed data with data **derived from the official SWDA Skills
Framework dataset** (downloaded and schema-verified in `.research/`), then upgrade the matcher
from a binary skill-set comparison to a **proficiency-aware** comparison (candidate proficiency
level vs required level, 1–6), with **bridges derived from shared Knowledge & Ability (K&A)
items** instead of hand-made, and **Emerging/CASL signals** surfaced from the official flags.
The 8-stage retrieval pipeline (BM25 + dense + RRF + cross-encoder) is kept intact; changes are
additive. ✅ **Implemented as described** (with one documented metric refinement — see Part D).

Confirmed decisions:
- **Sector scope:** re-ground the existing 5 sectors in real SWDA data (focused 5-sector demo;
  data layer stays 38-sector-capable). ✅
- **Depth:** data re-ground + proficiency + derived bridges; keep the pipeline and tests stable. ✅

### Verified ground truth (from `.research/inspect_report.txt`)
`skills_framework_dataset.xlsx` (13 MB, 6 sheets):
- `Job Role_Description` (2,030 roles): Sector | Track | Job Role | Job Role Description | Performance Expectation
- `Job Role_CWF_KT` (40,379 rows): Sector | Track | Job Role | Critical Work Function | Key Tasks
- `Job Role_TSC_CCS` (44,535 links): Sector | Track | Job Role | TSC_CCS Title | TSC_CCS Type | **Proficiency Level** | TSC_CCS Code
- `TSC_CCS_Key` (12,007 skills): TSC Code | Sector | Category | Title | Description | Type(tsc/ccs) | Latest Update Date
- `TSC_CCS_K&A` (150,264 rows): … | Proficiency Level | Proficiency Description | **Knowledge / Ability Items** | Classification

`unique_skills_list.xlsx` → `Unique Skills List` (2,316 skills): skill_title | skill_description |
skill_type | **Emerging Skills (0/1)** | **CASL Skills (0/1)**.

**Important nuance discovered during implementation:** TSC skills store numeric proficiency
(`1`–`6`), but **CCS (Critical Core Skills) store textual levels** (Foundation/Basic/Intermediate/
Advanced). The generator normalizes both onto the 1–6 scale (see Part C).

### Sector mapping (5 demo sectors → real SWDA sectors) — ✅ verified against all 38 sectors
| SkillBridge id | SWDA sector name(s) | Roles available |
|---|---|---|
| `finance` | Financial Services | 293 |
| `ict` | Infocomm Technology | 138 |
| `healthcare` | Healthcare | 77 |
| `engineering` | Engineering Services | 35 |
| `sustainability` | Carbon Services and Trading **+** Environmental Services (merged) | 8 + 30 |

Step 0 enumerated all 38 sectors and asserted every mapped name exists (`scripts/step0_explore.py`
→ `.research/step0_report.txt`). The 5 lowercase sector **ids** are unchanged, so `EXPECTED_SECTORS`,
the convergence test's 10 pairs, and the template color maps stay valid.

### Data model — additive, backward-compatible — ✅ implemented
`skills` stays a `list[str]` everywhere (BM25, dense search, and `result_card.html` consume it).
Proficiency is added as parallel dicts:
- **Candidate:** `skill_levels: {skill_title: proficiency_int}`; `skills` = its keys.
- **Job:** `skill_requirements: {skill_title: required_pl_int}` and `key_tasks: [str]`;
  `skills_required` = its keys (kept for compatibility).
- **New `app/data/skill_registry.json`:** `{skill_title: {type, description, category, sectors:[id…],
  emerging:bool, casl:bool, proficiency_descriptions:{"1".."6": str}}}`.

Counts kept at **150 candidates / 30 jobs** (re-grounded, not re-counted) so count assertions stay
green; the data layer remains trivially expandable to all 38 sectors.

### Generator `scripts/build_swda_seed.py` — ✅ implemented & run
Stdlib only (`zipfile` + `xml.etree`; **no pip**). Fixed `random.seed(20260729)`. Writes:
1. `skill_registry.json` 2. `skill_taxonomy.json` 3. `jobs.json` 4. `candidates.json`
5. `bridges.json` (K&A-derived) 6. `courses.json` (re-aligned keys).

### Pipeline changes (additive) — ✅ implemented
- `explainability.py` `run()` extended with optional `required_levels` / `candidate_levels`;
  keeps `matched`/`gap`/`bridge`; adds `matched_detail` and `proficiency_fit ∈ [0,1]` (or `None`).
- `orchestrator.py`: resolves required levels (seeded-job title match → real `skill_requirements`,
  else seniority heuristic), blends the display score (60% semantic + 40% proficiency fit, 40–98
  range), and emits `proficiency_fit`, `matched_detail`, `emerging_skills`, `casl_skills`.
- `bm25_search.py`, `dense_search.py`, `rrf_fusion.py`, `reranker.py`, `surprise_filter.py`,
  `sector_convergence.py` — **unchanged** (consume `skills`/taxonomy whose shape is preserved).

### API + template (additive) — ✅ implemented
- `schemas.py`: `MatchedSkillDetail` + optional `MatchResult.proficiency_fit / matched_detail /
  emerging_skills / casl_skills` (defaults keep `RESULT_FIELDS.issubset(...)` valid).
- `result_card.html`: PL-fit pill, Emerging/CASL badges, and `L{cand}≥/＜L{req}` annotations on
  matched chips (with graceful fallback when no proficiency data is present).

### Validator updates — ✅ implemented & passing
Kept `EXPECTED_CANDIDATES=150`, `EXPECTED_JOBS=30`, `EXPECTED_SECTORS`. Added `skill_levels` /
`skill_requirements` field + 1–6 range checks, `validate_skill_registry()`, and
`validate_cross_references()` (every candidate/job/bridge skill must exist in the registry).

### Test plan — ✅ **DONE (64 tests green)**
Keep data-independent tests untouched (`test_scaffold`, `test_rrf`, `test_surprise_filter`,
`test_sector_convergence`, tokenizer/structure tests). Updated the data-dependent tests to be
**data-driven** (real SWDA skill titles from the generated data):
- `test_explainability.py` — pick a real gap/via pair from generated `bridges.json`; use real
  registry skill titles; keep the structure test; add proficiency-fit tests.
- `test_course_mapper.py` — known-skill test picks a key from `courses.json`; counts stay
  150/30/≥30/≥30.
- `test_bm25.py` / `test_dense_search.py` — candidate count stays 150 (no change expected).
- `test_pipeline_e2e.py` — build `RANKED_JD` from a real seeded job (title + skills + description)
  so matched/gap/proficiency are meaningful; keep `total==10`, score 40–98, `len(courses)==len(gap)`;
  add `proficiency_fit ∈ [0,1]` and `matched_detail` PL-consistency assertions.
- New `test_skill_registry.py` — registry non-empty, flags are bools, proficiency descriptions
  present; bridges derived (`via != key`, `confidence ∈ [0,1]`).

**Run gate:** `python -m app.validate_seed_data` (✅ passing) then `pytest -q` (✅ **64 passed**, 44.9 s).

### Practical constraints — ✅ honored
- **No pip:** generator + all code use stdlib / installed deps only.
- **Flaky terminal:** long jobs run detached (`nohup setsid … & disown`) and logs polled via Read;
  recovered hung PTYs by launching a background command and observing the clean prompt.
- **Do not commit the 13 MB workbooks:** `.research/` added to `.gitignore`; generated
  `app/data/*.json` **are** committed.
- **Deterministic:** fixed random seed.

### Out of scope / assumptions
- Not expanding to all 38 sectors now (data layer is 38-capable; expansion = edit the sector map
  + re-run the generator).
- No real course-catalog download exists in the 3 datasets; course entries are grounded placeholders
  (real provider names + MySkillsFuture directory URLs) with the existing fallback behavior unchanged.
- Embedding/reranker models and Qdrant setup unchanged.

---

## Part B — Progress review (done vs yet-to-do)

### ✅ Done this phase
1. **Research grounded in real data.** Downloaded + schema-verified the 3 official SWDA workbooks;
   enumerated all 38 sectors; locked and verified the 5-sector mapping; sampled real roles, skills,
   proficiency levels, K&A items, and Emerging/CASL flags (`.research/step0_report.txt`).
2. **One-off generator (stdlib only).** `scripts/xlsx_util.py` (OOXML reader) +
   `scripts/build_swda_seed.py` (derives all 6 JSON files; deterministic seed).
3. **Regenerated seed data (real-world grounding):**
   - `jobs.json` — 30 real SWDA roles (e.g. *Account Operations Analyst*, *Carbon Accountant*,
     *Associate Security Analyst*) with real descriptions, key tasks, and `skill_requirements`
     (skill → required PL 1–6).
   - `candidates.json` — 150 candidates anchored to real roles, each with `skill_levels`
     (skill → candidate PL), realistic names/years/certifications/summaries.
   - `skill_registry.json` (NEW) — 434 skills with type, description, category, mapped sectors,
     Emerging/CASL flags (67 emerging, 82 CASL), and per-level proficiency descriptions.
   - `skill_taxonomy.json` — real TSC/CCS titles per sector (finance 70, ict 63, healthcare 80,
     engineering 64, sustainability 77).
   - `bridges.json` — **53 evidence-based bridges** derived from K&A containment (confidence
     0.20–0.87, mean 0.39), e.g. *AI Application ↔ AI Application in Product Development*,
     *Business Continuity Management ↔ Business Continuity Planning*.
   - `courses.json` — 434 SSG-style entries keyed to real skill titles (real providers +
     MySkillsFuture directory URLs).
4. **Proficiency-aware matching.** `explainability.py` (`matched_detail`, `proficiency_fit`) and
   `orchestrator.py` (required-level resolution, 60/40 hybrid score blend, Emerging/CASL surfacing).
5. **API + UI.** `schemas.py` additive fields; `result_card.html` PL-fit pill, Emerging/CASL badges,
   and `L≥L` proficiency annotations on matched skills.
6. **Data-quality gate.** `validate_seed_data.py` extended (proficiency ranges, registry, cross-refs)
   — **passes (exit 0)**.
7. **Hygiene.** `.gitignore` excludes `.research/` (13 MB workbooks + scratch); generated
   `app/data/*.json` remain committed.

### ⏳ Yet to do
_All implementation work is complete._ Remaining items are user-side / optional:
1. (Optional, user-side) Capture fresh screenshots/demo of the proficiency fit + Emerging/CASL badges.
2. (Optional, user-side) Refresh the Phase 3 CLI evidence (qodercli runs).

---

## Part C — Necessary information (technical reference)

### Source data (where it comes from)
- Portal: `https://jobsandskills.swda.gov.sg` (Skills & Workforce Development Agency × GovTech).
  Full research notes + the exact `file.go.gov.sg` download URLs are recorded in
  `docs/research/swda-jobs-and-skills-research.md` (§4 Downloadable data).
- Local copies (git-ignored, in `.research/`): `skills_framework_dataset.xlsx` (13 MB),
  `unique_skills_list.xlsx`, `tsc_unique_mapping.xlsx`.
- **To regenerate seed data:** place the three workbooks in `.research/` and run
  `python scripts/build_swda_seed.py` (stdlib only; ~20–40 s; writes the 6 JSON files and
  `.research/build_report.txt`).

### Proficiency scale (1–6, Bloom-like)
1 Use → 2 Operate → 3 Apply → 4 Implement → 5 Analyse → 6 Assess/Lead.
CCS textual levels are normalized: Foundation→1, Basic→2, Intermediate→3, Advanced→5
(`parse_pl()` in the generator; unknown defaults to 3).

### Matching algorithm (what changed and why)
- **Retrieval (unchanged):** BM25 top-50 + dense (all-MiniLM-L6-v2) top-50 → RRF (k=60) top-30 →
  cross-encoder (ms-marco-MiniLM-L-6-v2) top-10.
- **Proficiency-aware fit (new):** for each required skill, compare candidate PL vs required PL —
  full credit if `cand_pl ≥ req_pl`, partial credit `cand_pl/req_pl` if present below level, 0 if
  absent. `proficiency_fit` = mean credit over required skills (or `None` if no required levels).
- **Hybrid score (new):** `display = 40 + 58 × (0.6 × semantic_norm + 0.4 × proficiency_fit)`,
  semantic-only fallback when fit is `None`; stays in the 40–98 display range.
- **Required-level resolution for free-text JDs (new, deterministic):** (1) if a seeded job title
  appears in the JD text, reuse that job's real `skill_requirements`; (2) else infer one level from
  seniority cues — Junior/Associate→2, Mid/Engineer/Analyst→3 (default), Senior/Staff→4,
  Manager/Principal/Lead→5, Director/Head/Chief/Partner→6.
- **Derived bridges (new):** for each used skill S, the bridge `via` is the skill V whose K&A items
  best **cover** S — containment `|S ∩ V| / |S|` — emitted only above `BRIDGE_FLOOR = 0.2`; CCS
  `via` skills get a +0.1 boost (capped 0.95) because Critical Core Skills are officially
  cross-sector transferable. (See Part D for the Jaccard→containment refinement.)
- **Emerging/CASL signals (new):** surfaced from `unique_skills_list.xlsx` flags via the registry;
  shown as badges on the result card.

### File inventory (this phase)
| File | Change |
|---|---|
| `scripts/xlsx_util.py` | NEW — dependency-free OOXML reader (`Workbook`). |
| `scripts/step0_explore.py` | NEW — Step-0 sector enumeration/sampling. |
| `scripts/build_swda_seed.py` | NEW — seed-data generator (stdlib only, deterministic). |
| `app/data/skill_registry.json` | NEW — 434-skill registry (metadata + flags + PL descriptions). |
| `app/data/skill_taxonomy.json` | REGENERATED — real SWDA skill titles per sector. |
| `app/data/jobs.json` | REGENERATED — 30 real roles + `skill_requirements` + `key_tasks`. |
| `app/data/candidates.json` | REGENERATED — 150 candidates + `skill_levels`. |
| `app/data/bridges.json` | REGENERATED — 53 K&A-containment-derived bridges. |
| `app/data/courses.json` | REGENERATED — 434 entries keyed to real skill titles. |
| `app/data/__init__.py` | EDIT — added `get_skill_registry()`. |
| `app/pipeline/explainability.py` | EDIT — proficiency-aware `run()` + `_proficiency_analysis()`. |
| `app/pipeline/orchestrator.py` | EDIT — `_resolve_required_levels`, `_seniority_level`, `_blend_score`, new result fields. |
| `app/api/schemas.py` | EDIT — `MatchedSkillDetail` + additive `MatchResult` fields. |
| `templates/partials/result_card.html` | EDIT — PL-fit pill, Emerging/CASL badges, PL annotations. |
| `app/validate_seed_data.py` | EDIT — proficiency/registry/cross-reference checks. |
| `.gitignore` | NEW — excludes `.research/`, caches, `qdrant_data/`. |

### Verification status
- `python -m app.validate_seed_data` → **PASSED (exit 0)** — 150 candidates / 30 jobs, courses +
  bridges structure OK, no duplicate bridge keys, 5-sector taxonomy, registry + cross-references OK.
- `pytest tests/ -q` → ✅ **64 passed, 1 warning in 44.90 s** (exit 0). Suite includes:
  - 8 explainability tests (incl. 3 new proficiency-fit tests)
  - 7 skill-registry tests (new `test_skill_registry.py`)
  - 7 course-mapper tests, 5 BM25, 6 dense, 4 RRF, 4 surprise, 6 e2e, 4 scaffold, 13 convergence.

### Operational notes
- **Terminal flakiness (NixOS direnv):** the PTY frequently reports "Timed out waiting for terminal
  prompt after interrupting existing input (0ms)" and executes nothing. Reliable recipe: launch a
  throwaway **background** command, read `GetTerminalOutput` until the prompt shows direnv reloaded
  (`… via impure (nix-shell-env)`), then run the real command as a **finite foreground** command.
  For long jobs use `nohup setsid python X > log 2>&1 < /dev/null & disown` and poll the log via Read.
- **No pip** in the dev venv — all new code is stdlib / already-installed deps only.

---

## Part D — Decisions & deviations (explicit)
1. **Bridge metric refined from Jaccard to containment.** The approved spec said "Jaccard". Symmetric
   Jaccard over large K&A item sets produced many near-zero, meaningless bridges (mean 0.064; e.g.
   *3D Modelling → Robotic and Automation Technology Application* at 0.019). For *directional*
   bridging ("bridge gap S via skill V"), the appropriate measure is **containment** `|S ∩ V| / |S|`
   (fraction of the gap skill's competencies already covered by the via skill). With containment +
   a `0.2` evidence floor, the 53 emitted bridges are all sensible (mean 0.39, max 0.87). This serves
   the spec's stated goal of *evidence-based* bridges; reverting to literal Jaccard is a one-line
   change in `build_bridges()` if preferred.
2. **Counts kept at 150/30.** Re-grounding (not re-counting) preserves the count assertions in
   `test_bm25.py`, `test_course_mapper.py`, and the validator while delivering full real-world
   grounding. Expansion to more roles/sectors is a generator config change.
3. **Course entries are grounded placeholders.** The 3 official datasets contain no course catalog;
   entries use real provider names + MySkillsFuture course-directory search URLs, and the existing
   fallback behavior in `course_mapper.py` is unchanged. The live source for real course data is the
   MySkillsFuture course directory / SSG course search (noted in the research doc).
