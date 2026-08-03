#!/usr/bin/env python3
"""One-off migration: enrich all 150 candidate summaries from real data.

After ``fix_summaries.py`` trimmed the dangling ``[:140]`` fragments, 96 of 150
summaries were left without a role-description sentence (their official SWDA
descriptions open with a single sentence longer than 140 characters that lists
every alternate role title). The source workbooks are gone, so that exact text
cannot be recovered - but every candidate has plenty of *real* structured data
we can surface instead, with zero invented content:

- their actual top skills, now annotated with the real SWDA proficiency level
  (L1 Use -> L6 Assess/Lead) they already carry in ``skill_levels``;
- the real SWDA role description where it survived the trim, or the full
  official description from ``jobs.json`` when the candidate's title matches a
  curated role;
- otherwise, real skill breadth (their next-strongest SWDA skills);
- their real certifications.

The result reads like a genuine CV profile and never claims a skill, level or
credential the candidate does not have (no hallucination).

Run once::

    python scripts/enrich_summaries.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
CANDIDATES = DATA_DIR / "candidates.json"
JOBS = DATA_DIR / "jobs.json"


def _first_sentences(text: str, budget: int = 240) -> str:
    """Return complete sentences from ``text`` within ``budget`` characters.

    Never cuts mid-word or mid-sentence. Always includes the first sentence even
    if it exceeds the budget, so the result is always a complete thought ending
    in terminal punctuation (SWDA role descriptions often open with a single
    very long sentence listing every alternate role title).
    """
    text = " ".join((text or "").split())
    if not text:
        return ""
    sentences = [s.strip() for s in re.findall(r"[^.!?]+[.!?]", text) if s.strip()]
    if not sentences:
        # No terminal punctuation anywhere: treat the whole text as one sentence.
        return text.rstrip(".!?") + "."
    out: list[str] = []
    total = 0
    for s in sentences:
        if out and total + 1 + len(s) > budget:
            break
        out.append(s)
        total += len(s) + 1
    return " ".join(out)


def _join_and(items: list[str]) -> str:
    """'A', 'A and B', 'A, B and C'."""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _extract_intro(summary: str) -> str:
    """The '<Title> with N years in the <sector> sector.' lead sentence."""
    return summary.split("Strongest in", 1)[0].strip()


def _extract_role_desc(summary: str) -> str:
    """Any role-description sentence(s) after 'Strongest in <skills>. '."""
    m = re.search(r"Strongest in [^.]*\. (.+)$", summary, re.DOTALL)
    return m.group(1).strip() if m else ""


def enrich(candidate: dict, job_by_title: dict[str, dict]) -> str:
    """Build a rich, fully-grounded summary for one candidate."""
    summary = candidate.get("summary", "")
    intro = _extract_intro(summary)
    role_desc = _extract_role_desc(summary)

    # A role description lacking terminal punctuation is a broken truncation
    # artifact (the old [:140] slice); drop it so a clean source is used below.
    if role_desc and not role_desc.endswith((".", "!", "?")):
        role_desc = ""

    levels = candidate.get("skill_levels", {})
    ranked = sorted(levels, key=lambda s: -levels[s])
    top = ranked[:3]
    extra = ranked[3:6]

    strongest = ", ".join(f"{s} (L{levels[s]})" for s in top)

    # Role description priority: surviving real SWDA text > full jobs.json
    # description for a matching curated role > real skill breadth.
    if not role_desc:
        job = job_by_title.get(candidate.get("title", ""))
        if job and job.get("description"):
            role_desc = _first_sentences(job["description"], 180)
        elif extra:
            role_desc = f"Also proficient in {_join_and(extra)}."

    certs = candidate.get("certifications", [])
    cert_line = f"Holds {_join_and(certs)}." if certs else ""

    parts = [intro, f"Strongest in {strongest}."]
    if role_desc:
        parts.append(role_desc)
    if cert_line:
        parts.append(cert_line)
    return " ".join(p for p in parts if p)


def main() -> None:
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    jobs = json.loads(JOBS.read_text(encoding="utf-8"))
    job_by_title = {j["title"]: j for j in jobs}

    enriched = 0
    for cand in candidates:
        original = cand.get("summary", "")
        # Idempotency guard: skip summaries already enriched (carry '(L<n>)'
        # levels) AND clean (end in terminal punctuation). Broken ones -
        # enriched but truncated without a full stop - are rebuilt.
        already_enriched = re.search(r"Strongest in [^.]*\(L\d\)", original)
        ends_clean = original.rstrip().endswith((".", "!", "?"))
        if already_enriched and ends_clean:
            continue
        cand["summary"] = enrich(cand, job_by_title)
        enriched += 1

    CANDIDATES.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Enriched {enriched}/{len(candidates)} candidate summaries.")


if __name__ == "__main__":
    main()
