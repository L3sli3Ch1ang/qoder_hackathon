# SkillBridge SG

**Cross-sector skills matching for Singapore's workforce.**

> **Mission:** Make every transferable skill count — so no worker is invisible to the
> jobs they can already do.

**Hackathon:** Alibaba Cloud × Qoder Hackathon Singapore 2026
**Status:** v2.0 — working demo, 97 tests green, grounded in the official Skills &
Workforce Development Agency (SWDA) Skills Framework dataset.

---

## Development Environment (NixOS + direnv + flake)

This repository runs entirely on **NixOS** with **direnv** and **flake.nix**.
Every dependency — Python, Node, Bun, Qoder CLI, IDEs, vector DB — is
declaratively provisioned by the flake. No manual installs, no `apt`, no
`brew`.

### Repository layout

| Folder | Purpose | Activation |
|---|---|---|
| `qoder_desktop/` | Qoder Desktop (Electron) + Qdrant + full dev stack | `cd qoder_desktop` → direnv auto-loads `flake.nix` |
| `qoder_cli/` | SkillBridge app + Qoder CLI + FastAPI + Bun | `cd qoder_cli` → direnv auto-loads `flake.nix` |

### How it works

Each subfolder contains:
- **`flake.nix`** — declares the full dev shell (languages, tools, libraries,
  runtime library paths for C extensions).
- **`.envrc`** — contains `use flake`, which tells direnv to automatically
  activate the Nix flake shell whenever you `cd` into the directory.

```bash
# Just cd in — direnv activates the flake shell automatically
cd qoder_desktop    # Qoder Desktop + Qdrant + Qoder CLI + IDEs
cd qoder_cli        # Qoder CLI + FastAPI + Bun + Python + FFmpeg + Chromium
```

No `nix develop` wrapper needed — direnv handles it transparently.

---

## 1. Purpose & Objectives

### The problem

Singapore's SkillsFuture initiative actively encourages **cross-sector career
mobility**, yet mainstream job platforms (LinkedIn, MyCareersFuture, JobStreet)
match candidates to roles using **single-sector keyword overlap**. A professional
accountant with "data analytics + Python" is invisible to "Forensic Audit" or
"AI Governance" roles in Infocomm Technology — and vice-versa. These platforms
also treat a skill as binary (has / doesn't have), ignoring **how proficient**
the candidate actually is.

### What this app sets out to do

SkillBridge SG is a focused, working demonstration that:

1. **Understands transferable skills across sectors** — not just exact keyword
   matches, but semantic similarity and evidence-based "bridge" skills.
2. **Combines semantic understanding with strict, proficiency-weighted matching**
   — grounded in the official SWDA proficiency scale (levels 1–6).
3. **Explains every result** — which skills matched, which are gaps, which can be
   bridged, and which courses close those gaps. Nothing is a black box.
4. **Is accessible** to recruiters and career coaches without a data-science team.

### Objective measures of success

| # | Objective | How it is demonstrated |
|---|---|---|
| 1 | Paste a JD → ranked, explained results in **< 1 second** | Live app + latency tests |
| 2 | Scores are **proficiency-aware** (PL 1–6), grounded in official data | `matched_detail` per result |
| 3 | At least one result shows a **cross-sector bridge** | Bridge chips + confidence |
| 4 | Every recommendation traces to **real government data** | Data provenance (§4) |
| 5 | The matching engine is **inspectable and reproducible** | 97-test suite + deterministic seed |

---

## 2. What the app does (features)

### Core matching
- **Paste a Job Description → ranked candidate list.** A single `POST /api/match`
  runs the full 8-stage pipeline (§3) and returns the top-10 candidates, each with
  a 40–98 score, a 2-sentence narrative, and a full skills breakdown.
- **Proficiency-aware scoring.** Every matched skill shows the *required* proficiency
  level vs the *candidate's* level (PL 1–6), with full/partial/zero credit.
- **Explainability per result.** Matched skills, gap skills, and bridge skills are
  listed explicitly, each backed by the official SWDA taxonomy.
- **Course recommendations.** Every gap skill maps to a SkillsFuture-aligned course
  with a live MySkillsFuture search link.

### Recruiter & candidate tooling
- **What-if skill explorer.** The skills detected in the JD appear as checkboxes —
  **all checked by default** (every skill is folded into the match). A recruiter can
  uncheck skills they don't need, or press **Clear all** and then select just the one
  or two skills they want to prioritise. Scores re-run automatically and each card
  shows a ▲/▼ delta versus the previous run.
- **Hire ↔ Upskill perspective toggle.** The same results reframed for a *recruiter*
  ("who can do this job now") or a *candidate* ("what would it take to get there").
- **Surprise mode.** Re-sorts the top-10 by a semantic/lexical ratio to surface
  non-obvious, serendipitous candidates a keyword search would never show.
- **Emerging & CASL badges.** Skills flagged as *Emerging* or on the *Course
  Approval Skills List* in the official dataset are surfaced on each card.
- **Sector convergence strip.** A precomputed pairwise view of how much the five
  sectors' skill sets overlap (Jaccard over the taxonomy) — shows at a glance where
  cross-sector mobility is most natural.
- **Filters + light/dark theme.** Sector filters on results; token-based theming.

---

## 3. The matching engine (the core of the app)

This is the "main juice" — a production-style **hybrid retrieval pipeline** that
combines lexical recall, semantic recall, rank fusion, and neural re-ranking, then
layers on proficiency-aware scoring and explainability. Every stage is a small,
independently testable module under `app/pipeline/`.

### 3.1 The 8-stage pipeline

```
POST /api/match  →  PipelineOrchestrator (singleton)
  1. BM25Search            lexical recall, top-50      (rank_bm25)
  2. DenseSearch           semantic recall, top-50     (all-MiniLM-L6-v2 → Qdrant Lite, 384-dim, cosine)
  3. RRFFusion             merge + dedup, top-30       (Reciprocal Rank Fusion, k=60)
  4. CrossEncoderReranker  re-rank, top-10             (cross-encoder/ms-marco-MiniLM-L-6-v2)
  5. ExplainabilityEngine  matched / gap / bridge      (taxonomy-grounded + proficiency-aware, PL 1–6)
  6. SurpriseFilter        serendipity re-sort         (mode="surprise"; semantic/(lexical+ε))
  7. NarrativeGenerator    2-sentence explanation      (DashScope qwen-plus, parallel; offline fallback)
  8. CourseMapper          gap skill → SSG course      (MySkillsFuture directory URLs)
```

**Why hybrid?** Lexical (BM25) and semantic (dense) retrieval fail in different
ways. BM25 catches exact skill/title keywords but misses that "financial modelling"
is relevant to "valuation". Dense embeddings catch that transferable-skill
similarity but can drift off-topic. **Reciprocal Rank Fusion** merges the two ranked
lists robustly (no score normalisation needed), and a **cross-encoder** then scores
each surviving (JD, candidate) pair jointly for a precise final ranking. This is the
same recall → fuse → re-rank architecture used in production search systems.

### 3.2 Stage-by-stage detail

| # | Stage | Model / method | Input → Output | Key parameters |
|---|---|---|---|---|
| 1 | **BM25 lexical recall** | `rank_bm25` over tokenised skills · titles · summaries | query tokens → top-50 (`lexical_score`) | `BM25_TOP_K=50` |
| 2 | **Dense semantic recall** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) into **Qdrant Lite** (embedded, cosine) | query embedding → top-50 (`semantic_score`) | `DENSE_TOP_K=50` |
| 3 | **RRF fusion** | Reciprocal Rank Fusion: `score = Σ 1/(k + rank)` across both lists | two top-50 lists → deduped top-30 | `RRF_K=60`, `RRF_TOP_K=30` |
| 4 | **Cross-encoder re-rank** | `cross-encoder/ms-marco-MiniLM-L-6-v2` scores each (JD, candidate) pair | top-30 → top-10 (`cross_encoder_score`) | `RERANK_TOP_K=10` |
| 5 | **Explainability** | Taxonomy-grounded skill extraction + proficiency fit | top-10 → matched/gap/bridge + `proficiency_fit` | SWDA PL 1–6 |
| 6 | **Surprise filter** | `surprise = semantic / (lexical + ε)` re-sort | only in `mode="surprise"` | `ε = 1e-6` |
| 7 | **Narrative** | DashScope `qwen-plus` (parallel batch), offline template fallback | top-10 → 2-sentence explanation | anti-hallucination grounded |
| 8 | **Course mapping** | gap skill → MySkillsFuture search URL | gap list → course list | live directory links |

**Funnel:** 150 candidates → 50+50 recalled → 30 fused → 10 re-ranked → scored &
explained, in under a second.

### 3.3 Proficiency-aware scoring (the differentiator)

Binary "has the skill" matching is the weakness of existing platforms. SkillBridge
weights every skill by **proficiency** using the official SWDA scale:

> **Proficiency scale (1–6):** 1 Use → 2 Operate → 3 Apply → 4 Implement →
> 5 Analyse → 6 Assess/Lead.

**Required-level resolution** (deterministic, in `orchestrator.py`):
1. Start from a **seniority baseline** inferred from the JD text
   (Junior/Associate → 2, default → 3, Senior/Staff → 4, Manager/Lead → 5,
   Director/Head/Chief → 6).
2. If the JD mentions a **specific seeded SWDA job title** (≥ 2 words, word-boundary
   matched), overlay that role's authoritative `skill_requirements` (the exact PL
   from the official dataset) for the skills it requires. Every extracted skill is
   guaranteed a level, so What-if additions always influence the fit.

**Per-skill credit:**
- full credit `1.0` if `candidate_PL ≥ required_PL`
- partial credit `candidate_PL / required_PL` if the skill is present below the
  required level
- zero if the skill is absent

`proficiency_fit` = mean of the per-skill credits, in `[0, 1]`.

**Hybrid display score** (what the card shows, in `orchestrator._blend_score`):

```
semantic_norm = clamp((cross_encoder_score + 10) / 20, 0, 1)      # cross-encoder ~ -10..+10
combined      = 0.3 × semantic_norm + 0.7 × proficiency_fit        # skill match dominates
score         = int(40 + combined × 58)                            # display range 40–98
```

The **70% weight on proficiency fit** is deliberate: actual skill match dominates, so
a candidate whose profile text merely *resembles* the JD cannot outrank one who
actually has the matched skills. Falls back to semantic-only when no proficiency fit
is available. In ranked mode the final list is re-sorted by this blended score
(stable sort, cross-encoder order breaks ties).

### 3.4 Bridge skills (transferable-skill evidence)

A "bridge" answers: *the candidate lacks skill X, but has skill Y — how much of X is
already covered by Y?* Bridges are **derived, not invented**: for each gap skill `S`,
the seed builder finds the skill `V` whose official **Knowledge & Ability (K&A)
items** best *cover* `S`, using directional containment `|S ∩ V| / |S|`. Only bridges
clearing a `0.2` evidence floor are kept, and bridges via a **Critical Core Skill
(CCS)** get a `+0.1` boost (capped at 0.95) because CCS skills are officially
cross-sector transferable. Each bridge carries its confidence so the UI never shows a
meaningless near-zero link.

---

## 4. Data provenance — where everything comes from (not a black box)

A core goal is that **every number on screen traces back to official government
data**. All six seed files are generated by one deterministic, stdlib-only script —
`scripts/build_swda_seed.py` — from the **official SWDA Skills Framework dataset**.
Nothing is AI-hallucinated.

### 4.1 Source data

| Source | Contents |
|---|---|
| `skills_framework_dataset.xlsx` (13 MB, official SWDA) | ~150k rows: job roles, role descriptions, per-role skill requirements with proficiency levels, key tasks, skill metadata, and 150k+ Knowledge & Ability (K&A) items |
| `unique_skills_list.xlsx` (official SWDA) | Emerging Skills + CASL (Course Approval Skills List) flags per skill |

Source workbooks live in `.research/` (git-ignored due to size).

### 4.2 How each seed file is produced (`random.seed(20260729)` — fully reproducible)

| Seed file | Count | How it is derived |
|---|---|---|
| `jobs.json` | 30 real SWDA roles (6 × 5 sectors) | Selected deterministically (sort + stride) from roles with ≥ 5 skills. `skill_requirements` (skill → PL) taken **verbatim** from the "Job Role_TSC_CCS" sheet; `key_tasks` from "Job Role_CWF_KT"; descriptions from "Job Role_Description". |
| `candidates.json` | 150 profiles (30 × 5 sectors) | **Deterministic synthesis anchored to real roles.** Each candidate is anchored to a real SWDA role (`pool[i % len(pool)]`), then covers ~78% of that role's required skills (`random.random() < 0.78`) at a proficiency varied around the role's required level. Names/certifications come from fixed multicultural pools. The *skills and levels are real-role-derived* — only the person is synthetic. |
| `skill_registry.json` | 434 skills | type / description / category / sectors from "TSC_CCS_Key"; Emerging & CASL flags from "Unique Skills List"; per-level proficiency descriptions from "TSC_CCS_K&A". |
| `skill_taxonomy.json` | 5 sectors | Union of real TSC/CCS skill titles across each sector's selected jobs (finance 70, ict 63, healthcare 80, engineering 64, sustainability 77). |
| `bridges.json` | 53 bridges | K&A containment `|S∩V|/|S|` (see §3.4), floor 0.2, CCS +0.1 boost. Confidence ∈ [0.2, 0.95]. |
| `courses.json` | 434 entries | Grounded placeholders keyed to real skill titles; realistic Singapore providers; **live** MySkillsFuture search URLs (`courses.myskillsfuture.gov.sg/search?q=<skill>`). |

### 4.3 Reliability guarantees

- **Deterministic & reproducible:** fixed seed `20260729`; re-running the builder
  yields byte-identical output.
- **Auditable:** every job's skills/PLs are verbatim from the official dataset; every
  bridge has an explicit K&A evidence score.
- **Validated:** `python -m app.validate_seed_data` is a data-quality gate (unique
  JSON keys, proficiency ranges 1–6, registry structure, cross-file skill references)
  that must exit 0.
- **Candidates are illustrative, not real people** — but their skill profiles are
  anchored to real role requirements, so matching behaviour is realistic.

---

## 5. What the app CAN and CANNOT do

Being explicit about scope keeps the demo honest and points to where future
investment goes (§7).

### ✅ Can deliver

- Match a pasted JD to the candidate pool with **explainable, proficiency-aware
  scores** in under a second.
- Surface **transferable / bridge skills across 5 sectors** with evidence-backed
  confidence.
- Show **gap skills** and map each to a **SkillsFuture course**.
- Run **What-if simulations** (add/remove skills, see scores shift ▲/▼).
- Reframe results for **Hire vs Upskill** and surface **Surprise** candidates.
- Run **fully offline** — with no DashScope key, narratives fall back to a grounded
  template and the whole pipeline still works end-to-end.
- Be **reproduced and inspected** — deterministic seed data + 97-test suite.

### ❌ Cannot deliver (current limitations)

- **Not a production talent pool.** Demo-scale data: 150 candidates, 30 jobs,
  5 sectors (drawn from a dataset covering 2,030 roles / 12,007 skills).
- **Candidates are synthetic** (deterministic, SWDA-anchored) — not real people or
  resumes.
- **Paste-text input only.** No file upload, PDF/DOCX parsing, or live resume
  ingestion.
- **Skill extraction is taxonomy matching, not open-ended NLP.** It recognises the
  434 seeded SWDA skill titles (case-insensitive substring); skills outside the
  taxonomy are not detected.
- **Narratives are generated text** (qwen-plus, or a template offline). They are
  grounded in the matched data and are explanatory — the *score* is computed from
  structured skill/proficiency data, not from the LLM.
- **Scores are a demo ranking aid**, not a validated psychometric or hiring
  decision instrument.
- **No persistence, auth, or multi-user accounts.** Single-process demo.
- **Static seed data** — no live sync with MySkillsFuture or SWDA portals.
- **Course links are search results**, not specific course enrolments.

---

## 6. Architecture & technology stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Jinja2 (single process) |
| Frontend | Alpine.js + HTMX-style `fetch` + Tailwind (CDN) |
| Lexical search | `rank_bm25` (Python) |
| Dense embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector store | Qdrant Lite (embedded, zero-infra) |
| Cross-encoder | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| LLM narrative | Alibaba Cloud DashScope (`qwen-plus`); offline template fallback |
| Seed data | Official SWDA Skills Framework dataset (3 xlsx workbooks) |
| Environment | NixOS + direnv + flake.nix (Python 3.13) |

```
app/
  main.py                 FastAPI app, lifespan (builds orchestrator), /health, /
  config.py               Settings (pydantic-settings, env_prefix="SKILLBRIDGE_")
  validate_seed_data.py   data-quality gate
  api/routes.py           POST /api/match (HTMX partial vs JSON), error handling
  api/schemas.py          MatchRequest / MatchResponse / MatchResult / ...
  data/__init__.py        lru_cache JSON loaders
  data/*.json             seed corpus (§4)
  pipeline/*.py           the 8 stages + orchestrator + sector_convergence
scripts/
  build_swda_seed.py      deterministic generator: SWDA workbooks → 6 seed JSONs
  xlsx_util.py            dependency-free OOXML reader (stdlib zipfile + ElementTree)
templates/                base.html, index.html, partials/
tests/                    pytest suite (97 tests)
```

### Configuration

All settings in `app/config.py`, overridable via env vars prefixed `SKILLBRIDGE_`:

| Setting | Default |
|---|---|
| `MODEL_EMBEDDING` | `sentence-transformers/all-MiniLM-L6-v2` |
| `MODEL_RERANKER` | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `BM25_TOP_K` / `DENSE_TOP_K` / `RRF_TOP_K` / `RERANK_TOP_K` / `RRF_K` | 50 / 50 / 30 / 10 / 60 |
| `DASHSCOPE_API_KEY` | `""` (empty → offline narrative fallback) |
| `DASHSCOPE_MODEL` | `qwen-plus` |

For the Alibaba Cloud *international* endpoint, set
`SKILLBRIDGE_DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.

---

## 7. Running & testing

```bash
cd qoder_cli                                             # direnv auto-activates the flake shell
uv pip install -r requirements.txt                       # if the venv needs deps
uvicorn app.main:app --host 127.0.0.1 --port 8000        # serve (first start indexes Qdrant)
# Open http://127.0.0.1:8000 → paste a JD → see ranked results

pytest tests/ -v                                         # 97 tests, all green
python -m app.validate_seed_data                         # data-quality gate, exit 0
```

Regenerate seed data (requires the official workbooks in `.research/`):

```bash
python scripts/build_swda_seed.py                      # stdlib only, deterministic
```

---

## 8. Roadmap — where to invest next

If more resources are added, these are the highest-leverage improvements, in priority
order:

1. **Real candidate ingestion.** Parse real resumes (PDF/DOCX) and map them onto the
   SWDA taxonomy (replace the synthetic candidate pool).
2. **Scale the corpus.** Expand from 5 demo sectors toward the full 38 SWDA sectors
   (2,030 roles / 12,007 skills) and a larger candidate pool; move Qdrant Lite →
   Qdrant server.
3. **Richer skill extraction.** Add NER/embedding-based skill detection so skills
   phrased outside the taxonomy are still recognised.
4. **Live data sync.** Periodically re-derive seeds from updated SWDA/MySkillsFuture
   releases.
5. **Persistence & accounts.** Save searches, track candidate pipelines, multi-user.
6. **Outcome feedback loop.** Record which matches led to hires to tune the blend
   weights and bridge thresholds.
7. **Bias & fairness review.** Audit the scorer for sector/seniority bias before any
   real hiring use.

---

## 9. Related documents

| Document | Purpose |
|---|---|
| `spec.md` | Hackathon submission write-up (problem, solution, status, checklist) |
| `AGENTS.md` | AI-agent working guide (architecture, config, testing conventions, pitfalls) |
| `spec-video.md` | Demo video scene-by-scene breakdown |
| `CHANGELOG.md` / `RELEASE_NOTES.md` | Version history |
| `docs/evidence/` | Progress log, per-phase notes, code reviews (Qoder usage evidence) |
| `docs/research/` | SWDA portal research (downloads, tools, 38-sector list) |
