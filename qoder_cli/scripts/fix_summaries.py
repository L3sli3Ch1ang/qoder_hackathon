#!/usr/bin/env python3
"""One-off migration: repair truncated candidate summaries.

The seed builder hard-cut the official SWDA role description at 140 characters
(``description[:140]``), which frequently severed the text mid-word or
mid-sentence, e.g.::

    "...assumes the respo"
    "...He/She formulat"

That made the "View full profile" summary read as nonsense. The source
workbooks are no longer available, so the lost tail cannot be recovered.
Instead we trim every summary back to the last *complete* sentence so each one
ends cleanly and still makes sense. This is deterministic and introduces no new
text (no hallucination) - it only removes the dangling fragment.

Run once::

    python scripts/fix_summaries.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "app" / "data" / "candidates.json"


def clean_summary(summary: str) -> str:
    """Return a summary that ends at a complete sentence boundary.

    - Already ends with a full stop  -> unchanged.
    - Ends mid-sentence/mid-word     -> trimmed back to the last ". " so the
      text stops at the end of the previous complete sentence.
    """
    s = (summary or "").strip()
    if not s or s.endswith("."):
        return s
    cut = s.rfind(". ")
    if cut != -1:
        return s[: cut + 1]  # keep the full stop
    return s


def main() -> None:
    candidates = json.loads(DATA.read_text(encoding="utf-8"))
    fixed = 0
    for cand in candidates:
        original = cand.get("summary", "")
        cleaned = clean_summary(original)
        if cleaned != original:
            cand["summary"] = cleaned
            fixed += 1
    DATA.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Repaired {fixed}/{len(candidates)} candidate summaries.")


if __name__ == "__main__":
    main()
