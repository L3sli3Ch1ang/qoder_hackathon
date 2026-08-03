# SkillBridge Release Notes

## 2026-08-03

### Headline

This release makes the two things judges most need to trust — **how the matching
engine works** and **where the data comes from** — explicit across the app, the
demo video, and the submission documents, and adds comprehensive reference
documentation.

### Added

- **README.md** — the single reference for the app: mission & objectives, the
  8-stage matching engine (exact models, parameters, scoring formula), data
  provenance (deterministic, SWDA-grounded, not AI-hallucinated), the full feature
  list, explicit can / cannot boundaries, and a roadmap for future investment.

- **What-if skill explorer UX** — detected JD skills now start **checked by
  default** with a **Clear all** button, so a recruiter can uncheck the one or two
  skills they don't need, or clear everything and pick just the one or two to
  prioritise. Scores re-run automatically with ▲/▼ deltas.

- **Candidate full-profile modal** — `GET /candidate/{id}` returns the complete CV
  so the narrative's claims can be checked against the candidate's actual skills,
  proficiency levels, certifications, and summary.

- **Demo video re-cut (15 scenes, 180 s)** — new **Matching Engine** deep-dive and
  **Data Provenance** scenes, plus a mission statement opening and a purpose-led
  close.

### Changed

- **Scoring now weights real skill match at 70%** (was 60% semantic / 40% fit; now
  30% / 70%), and ranked results are re-sorted by the blended score — so a profile
  that merely *reads like* the JD can no longer outrank one that actually has the
  matched skills.

- **Anti-hallucination narratives** — the LLM is told to reference only the
  verified matched / gap skills; the offline fallback cites the candidate's real
  profile skills.

- **Faster result load** — with no DashScope key, narratives short-circuit to the
  offline template instead of attempting a batch of failing HTTP calls.

### Fixed

- Corrected the documented blend weights (0.3 / 0.7) and the video scene breakdown
  in `spec.md` / `spec-video.md`, and added a prominent mission statement.

### Tests

- Suite expanded to **97 tests**.

---

## 2026-07-31

### Fixed

- **What-If skill removal is now case-insensitive and taxonomy-aware.**
  Previously `removed_skills` used exact-case `str.replace`, so a removed skill
  could remain in the processed JD text or accidentally clip a longer,
  distinct taxonomy skill title. Removal now mirrors the case-insensitive
  behavior of `extract_skills`, preserves standalone mentions inside longer
  skill titles, and explicitly drops removed skills from the extracted JD
  skill set.

- **Narrative score now matches the displayed score.**
  The DashScope prompt used to derive its own "% match" from the raw
  cross-encoder score, which could disagree with the blended score shown on
  the result card. The display score (60% semantic + 40% proficiency fit) is
  now computed once in the orchestrator and passed to the narrative
  generator, so the narrative always quotes the same percentage the UI
  displays.

### Added

- `tests/test_whatif_removal.py` — 5 data-driven unit tests covering
  case-insensitive removal, longer-title preservation, mid-word safety, and
  regex metachar escaping.

- `tests/test_narrative_score_e2e.py` — hermetic end-to-end integration test
  that drives the full `/api/match` pipeline with a stubbed DashScope client
  and verifies the narrative's "% match" equals the displayed `score` in both
  `ranked` and `surprise` modes.

- Test suite expanded from 64 to **71 tests**.

### Changed

- AGENTS.md rewritten to the minimal agent-guidance format: removed the
  file-by-file layout and documentation map, added the standard prefix, and
  kept only the non-obvious gotchas an AI agent would get wrong without it.

- `app/pipeline/narrative.py` now reuses a single `httpx.AsyncClient` across
  the batch of narrative calls instead of creating one per candidate.

### Internal cleanup

- Removed unused `jd_set` variable in `app/pipeline/explainability.py`.
- Corrected `_extract_jd_title` docstring to match the 80-character truncation
  behavior in `app/pipeline/orchestrator.py`.

---

*See [CHANGELOG.md](CHANGELOG.md) for the full project history.*
