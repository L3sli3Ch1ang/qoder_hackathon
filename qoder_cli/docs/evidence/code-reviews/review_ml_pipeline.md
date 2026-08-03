# Code Review — ML Pipeline

**Scope:** `app/pipeline/` — `bm25_search.py`, `dense_search.py`, `rrf_fusion.py`, `reranker.py`,
`explainability.py`, `surprise_filter.py`, `narrative.py`, `course_mapper.py`, `orchestrator.py`.

## Summary
The pipeline is a clean, well-separated implementation of the spec's 8-stage hybrid retrieval
design. Each stage is a single-responsibility class with a `run(...)` method; the orchestrator
composes them. Models and all tuning knobs are externalised to `app/config.py`.

## Strengths
- **Correct stage ordering.** Recall (BM25 ∥ dense) → RRF fusion → cross-encoder rerank →
  explainability → (optional) surprise → narrative → course mapping. Cheap recall first, expensive
  cross-encoder only on the fused top-30, narrative only on the final top-10.
- **Configurable model paths & parameters.** `MODEL_EMBEDDING`, `MODEL_RERANKER`, `QDRANT_PATH`,
  and all top-K / RRF-k values live in `Settings` (env-overridable via `SKILLBRIDGE_` prefix), so
  models can be swapped without code changes.
- **Graceful narrative degradation.** `NarrativeGenerator` uses an offline template fallback when
  `DASHSCOPE_API_KEY` is empty or the API call fails — the pipeline never hard-fails on LLM outage,
  and tests run hermetically with no key.
- **Efficient vector store.** `DenseSearch._ensure_collection` indexes once and short-circuits when
  `points_count >= len(candidates)`, avoiding re-embedding on every start (covered by
  `tests/test_dense_search.py::test_collection_reused_not_reindexed`).
- **Numerical safety.** `SurpriseFilter` guards division with `EPSILON`; `_normalize_score` clamps
  to a sane 40–98 display range.

## Findings
| # | Severity | File | Finding | Resolution |
|---|----------|------|---------|------------|
| 1 | **High** | `orchestrator.py` | Surprise mode rebuilt the result list by zipping the surprise-re-ordered `top_candidates` with the original-order `skills_list`, so each surprise card showed a *different* candidate's matched/gap/bridge skills. | **Fixed** — after `surprise_filter.run(...)`, rebuild `skills_list = [c["skills_analysis"] for c in top_candidates]`. Regression test added (`test_pipeline_e2e.py::test_surprise_skills_align_to_correct_candidate`). |
| 2 | Low | `narrative.py` | The live-API `score` derivation duplicates the orchestrator's normalisation and is only used in the prompt string. | Acceptable for a demo; could reuse `_normalize_score`. No action required. |
| 3 | Low | `dense_search.py` | Embedding model + Qdrant client are constructed in `__init__`, so import-time side effects are heavy. | Mitigated by the singleton orchestrator (built once at lifespan startup). |

## Recommendations
- Persist the normalised display score source-of-truth in one place (orchestrator) and have the
  narrative consume it, removing the duplicated heuristic in `narrative.py`.
- If recall grows, consider batching the cross-encoder `predict` call.

## Verdict
✅ **Approve.** The High-severity alignment bug is fixed and regression-tested; the pipeline is
otherwise sound, configurable, and resilient.
