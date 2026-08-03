# Code Review — Backend API

**Scope:** `app/main.py`, `app/api/routes.py`, `app/api/schemas.py`, `app/config.py`,
`app/data/__init__.py`.

## Summary
A small, conventional FastAPI backend. Routing is RESTful, request/response contracts are enforced
by pydantic, and errors are handled gracefully for both HTMX and JSON clients.

## Strengths
- **RESTful, content-negotiated endpoint.** `POST /api/match` returns an HTML partial for
  `HX-Request: true` clients and a typed `MatchResponse` otherwise — one route serves both the
  HTMX-style front end and programmatic consumers.
- **Strong validation.** `MatchRequest` enforces `jd_text` `min_length=1`, a `Literal` mode
  (`ranked`/`surprise`), a `Literal` perspective (`recruiter`/`candidate`, default `recruiter`), and
  list fields with safe defaults. Empty input is rejected with a 422 (verified in
  `tests/test_pipeline_e2e.py::test_empty_jd_rejected_with_422`), never a 500.
- **Graceful error handling.** The route wraps the pipeline in try/except and returns a structured
  error (HTML error banner for HTMX, JSON `{error, results: [], total: 0}` otherwise) with logging.
- **Settings hygiene.** `Settings` uses `env_prefix="SKILLBRIDGE_"`, preventing collisions with
  host environment variables; secrets (`DASHSCOPE_API_KEY`) default to empty.
- **Startup initialisation.** The orchestrator singleton is built once during the FastAPI lifespan,
  so the first request isn't paying model-load latency.

## Findings
| # | Severity | File | Finding | Resolution |
|---|----------|------|---------|------------|
| 1 | **Med** | `main.py`, `routes.py` | `TemplateResponse` was called with the legacy `(name, context)` signature, deprecated/broken in current Starlette. | **Fixed** — migrated to `TemplateResponse(request, name, context)` everywhere. |
| 2 | Low | `routes.py` | The error branch returns HTTP 200 for HTMX with an error banner (intentional, so the partial swaps in) but JSON errors also return 200. | Acceptable for a demo; a 5xx would be more REST-pure for JSON clients. |
| 3 | Low | `data/__init__.py` | `lru_cache` loaders mean seed data is read once per process; edits require a restart. | Intended behaviour; documented. |

## Recommendations
- Consider returning a proper 5xx for unexpected JSON errors while keeping the 200-with-banner
  behaviour for HTMX.
- Add a request-id / structured log line on the error path for easier demo debugging.

## Verdict
✅ **Approve.** RESTful design, pydantic validation, and dual-client error handling are solid; the
`TemplateResponse` signature issue is fixed.
