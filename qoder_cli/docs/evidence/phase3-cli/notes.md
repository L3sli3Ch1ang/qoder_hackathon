# Phase 3 — CLI Automation (qodercli) · Notes

**Goal:** Demonstrate the Qoder CLI (`qodercli`) driving the project from the terminal —
automated test execution, isolated branching, code review, and knowledge persistence.
This is spec Section 10 / Phase 3 and feeds the **30% "built with Qoder"** judging criterion.

> **Status:** User-side deliverable. `qodercli` is provisioned by the Nix dev shell
> (`flake.nix` → Numtide `llm-agents.nix` → `qoder-cli`). Open a terminal in this folder —
> direnv (`use flake`) activates the shell automatically — then run the four commands below
> and capture the listed screenshots. This file is the script; the screenshots + log entries
> are the evidence.

## Environment
```bash
cd <project folder>        # direnv activates the flake shell (Python 3.13, uv, qodercli)
qodercli --version         # sanity check the CLI is on PATH
```
No `nix develop` wrapper is needed inside this folder — direnv pre-loads the cached shell
(`VIRTUAL_ENV` + `LD_LIBRARY_PATH` exported). If a command hangs with
`Timed out waiting for terminal prompt …`, a stray background server is likely holding the
terminal/Qdrant lock; a `^C` clears it (see progress-log 2026-08-03 "Final gate").

## The four canonical CLI actions (spec Phase 3)

| # | Command | Demonstrates | Capture |
|---|---------|--------------|---------|
| 1 | `qodercli -p "run pytest tests/ -v and report failures"` | CLI-driven test automation | `screenshot_cli_tests.png` + pass/fail counts |
| 2 | `qodercli --worktree feature-explainability` | Isolated branch for a feature | `screenshot_cli_worktree.png` + branch purpose |
| 3 | `/review` (inside qodercli, scope `app/pipeline/`) | Automated code review before merge | `screenshot_cli_review.png` + issues found/fixed |
| 4 | `/init` | Generate `AGENTS.md` for knowledge persistence | terminal + generated `AGENTS.md` |

### 1. Run tests via CLI
```bash
qodercli -p "run pytest tests/ -v and report failures"
```
Expected: the suite reports **54 passed** (unit + dense + e2e + surprise regression + sector
convergence). Log the pass/fail counts.
📸 `docs/evidence/phase3-cli/screenshot_cli_tests.png`

### 2. Create an isolated worktree
```bash
qodercli --worktree feature-explainability
```
Purpose: develop/verify the explainability engine on an isolated branch without disturbing the
main working tree. Log the branch name + purpose.
📸 `docs/evidence/phase3-cli/screenshot_cli_worktree.png`

### 3. Run `/review` on the ML pipeline
Inside the CLI session, run `/review` scoped to `app/pipeline/`. Save the full output — it is
itself a code-review artifact.
- Raw CLI output → paste into `docs/evidence/phase3-cli/cli_review_output.md`.
- Curated findings → `docs/evidence/code-reviews/review_ml_pipeline.md` (already populated:
  High-severity surprise-alignment bug found + fixed + regression-tested; verdict Approve).

Log issues found and fixes applied (before/after diff).
📸 `docs/evidence/phase3-cli/screenshot_cli_review.png`

### 4. Generate `AGENTS.md` via `/init`
```bash
qodercli            # then run /init
```
`/init` persists project knowledge to `AGENTS.md` (architecture, config table, data + API
contract, run/test commands, testing conventions, known pitfalls). The generated file is committed
at the repo root: [`AGENTS.md`](../../../AGENTS.md).
📸 terminal showing `/init` + `AGENTS.md` content (also referenced by phase4-knowledge).

## Testing gate at this phase (spec)
| Test | Command | Pass criteria |
|------|---------|---------------|
| Full suite green via CLI | `qodercli -p "run pytest tests/ -v and report"` | 0 failures after review fixes |
| Explainability engine | `pytest tests/test_explainability.py -v` | returns matched/gap/bridge arrays |
| RRF fusion | `pytest tests/test_rrf.py -v` | dedups, respects k=60 |
| Pipeline e2e (API) | `pytest tests/test_pipeline_e2e.py -v` | POST /api/match → Top-10 with explanations |

## Evidence checklist
- [ ] `screenshot_cli_tests.png`
- [ ] `screenshot_cli_worktree.png`
- [ ] `screenshot_cli_review.png`
- [ ] `cli_review_output.md` (raw `/review` paste)
- [ ] `AGENTS.md` regenerated/confirmed via `/init`
- [ ] progress-log.md Phase 3 entries filled with actual counts + screenshot refs
