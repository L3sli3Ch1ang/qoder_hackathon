# Phase 1 — Specification · Notes

**Goal:** Define SkillBridge and lock the acceptance gates before writing code.

## What was produced
- `spec.md` — full product + engineering specification:
  - Problem framing: skills → jobs "hidden path" across 5 Singapore sectors
    (Finance, ICT, Healthcare, Engineering, Sustainability), SkillsFuture-aligned.
  - 8-stage hybrid pipeline: BM25 + dense (MiniLM + Qdrant Lite) → RRF (k=60) →
    cross-encoder rerank → explainability → surprise filter → DashScope narrative → course mapper.
  - Front end: FastAPI + Jinja2 + HTMX-style fetch + Alpine.js + Tailwind (CDN).
  - Section-10 documentation/evidence requirements (this tree).
- Repository scaffold: `app/main.py`, `app/config.py`, `app/data/__init__.py`, pipeline stubs,
  `tests/test_scaffold.py`.

## Key decisions
- **Hybrid retrieval** (lexical + semantic + RRF) chosen over pure-vector search so that exact
  skill keywords and semantic transferability both influence recall.
- **Qdrant Lite (embedded)** chosen over a hosted vector DB for a zero-infra, single-process demo.
- **Template-fallback narrative** so the app runs end-to-end with no API key (hermetic tests / offline demo).
- **`SKILLBRIDGE_` env prefix** for all settings (pydantic-settings) to avoid colliding with host env.

## Verification
- `tests/test_scaffold.py` green: imports, config load, app start, `/health`.

## Screenshot evidence (to be filled by user)
> Replace each placeholder with the captured Qoder desktop screenshot path.

- [ ] _Screenshot: spec.md authored in Qoder_ — `docs/evidence/phase1-spec/screenshots/spec_in_qoder.png`
- [ ] _Screenshot: scaffold tests passing_ — `docs/evidence/phase1-spec/screenshots/scaffold_tests.png`
