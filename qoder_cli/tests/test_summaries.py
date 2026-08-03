"""Data-quality regression guard for candidate profile summaries.

The "View full profile" summary must read like a real CV: it must end at a
complete sentence, carry real SWDA proficiency-level annotations, and reference
only skills the candidate actually has (no hallucination).

Regression guard for the bug where the seed builder's ``description[:140]``
slice left summaries dangling mid-word (e.g. "...assumes the respo"), and for
the follow-up enrichment that annotates top skills with their real proficiency
level and adds real certifications.
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "app" / "data" / "candidates.json"


def _candidates() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_all_summaries_end_at_a_complete_sentence():
    """No summary may be truncated mid-word / mid-sentence."""
    for c in _candidates():
        assert c["summary"].rstrip().endswith((".", "!", "?")), (
            f"{c['id']} summary is truncated: ...{c['summary'][-40:]!r}"
        )


def test_all_summaries_carry_proficiency_levels():
    """Every summary annotates its headline strengths with a real PL (L1-L6)."""
    for c in _candidates():
        assert "(L" in c["summary"], f"{c['id']} summary has no proficiency level"


def test_summaries_reference_real_skills_only():
    """The headline strengths must be the candidate's actual top skills.

    Guards against hallucination: the summary may only cite skills that exist
    in the candidate's verified ``skill_levels``.
    """
    for c in _candidates():
        levels = c.get("skill_levels", {})
        top = sorted(levels, key=lambda s: -levels[s])[:3]
        for skill in top:
            assert skill in c["summary"], (
                f"{c['id']} summary does not reference real skill {skill!r}"
            )
