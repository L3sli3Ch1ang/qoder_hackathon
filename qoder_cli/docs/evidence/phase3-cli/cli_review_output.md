# Phase 3 — `/review` raw CLI output (ML pipeline)

> Paste the full terminal output of `qodercli`'s `/review` (scoped to `app/pipeline/`) below.
> This raw capture is the spec-required "`/review` output" artifact. The curated, formatted
> findings live in [`../code-reviews/review_ml_pipeline.md`](../code-reviews/review_ml_pipeline.md).

**Command:** `/review` (inside `qodercli`, scope: `app/pipeline/`)
**Date:** _fill in at run time_
**Reviewer:** Qoder CLI

---

## Raw output

```text
<paste the /review terminal output here>
```

## Issues found → fixes applied

| #   | Severity | Finding                                                                                                                                                                                 | Fix (before → after)                                                                                                                                                                                      |
| --- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | High     | Surprise mode zipped the surprise-re-ordered `top_candidates` against the original-order `skills_list`, so each surprise card showed a different candidate's matched/gap/bridge skills. | Rebuild `skills_list = [c["skills_analysis"] for c in top_candidates]` after `surprise_filter.run(...)`; regression test added (`test_pipeline_e2e.py::test_surprise_skills_align_to_correct_candidate`). |
| —   | —        | _add rows from the live `/review` run_                                                                                                                                                  | —                                                                                                                                                                                                         |

## Test coverage snapshot (which stages have tests)

| Stage                | Test file                                                             |
| -------------------- | --------------------------------------------------------------------- |
| BM25 recall          | `tests/test_bm25.py`                                                  |
| Dense recall         | `tests/test_dense_search.py`                                          |
| RRF fusion           | `tests/test_rrf.py`                                                   |
| Cross-encoder rerank | _no dedicated unit test — exercised via `tests/test_pipeline_e2e.py`_ |
| Explainability       | `tests/test_explainability.py`                                        |
| Surprise filter      | `tests/test_surprise_filter.py`                                       |
| Course mapper        | `tests/test_course_mapper.py`                                         |
| Sector convergence   | `tests/test_sector_convergence.py`                                    |
| End-to-end (API)     | `tests/test_pipeline_e2e.py`                                          |
