# Phase 4 — Knowledge (Quest Knowledge hub) · Notes

**Goal:** Capture reusable project knowledge as Quest Knowledge hub cards so future sessions
(and teammates) inherit the architecture, conventions, and run commands.

> **Status:** User-side deliverable. Knowledge cards are authored in the Qoder Quest Knowledge
> hub. The content below is the source material; copy each card into the hub and attach screenshots.

## Suggested knowledge cards
1. **SkillBridge architecture** — 8-stage hybrid pipeline; singleton orchestrator; FastAPI + Jinja
   + HTMX + Alpine + Tailwind; Qdrant Lite embedded store.
2. **Models & config** — embeddings `all-MiniLM-L6-v2` (384-dim), reranker
   `cross-encoder/ms-marco-MiniLM-L-6-v2`, narrative `qwen-plus` via DashScope; all settings under
   the `SKILLBRIDGE_` env prefix (`app/config.py`).
3. **Run & test commands** — `nix develop`; `uvicorn app.main:app`; `pytest tests/ -v`;
   `python -m app.validate_seed_data`.
4. **Testing conventions** — hermetic tests monkeypatch `settings.QDRANT_PATH` to a temp dir (avoid
   the dev-server file lock) and blank `SKILLBRIDGE_DASHSCOPE_API_KEY` (force offline narrative);
   reset `PipelineOrchestrator._instance` between orchestrator builds.
5. **Known pitfalls** — Qdrant Lite holds a per-directory file lock (one process at a time);
   `json.load` silently collapses duplicate object keys (guard with `object_pairs_hook`).

## Screenshot evidence (to be filled by user)
- [ ] _Screenshot: Quest Knowledge hub cards for SkillBridge_ — `docs/evidence/phase4-knowledge/screenshots/knowledge_hub.png`
- [ ] _Screenshot: a knowledge card referenced in a new session_ — `docs/evidence/phase4-knowledge/screenshots/knowledge_in_use.png`
