"""One-off migration: rewrite course URLs in app/data/courses.json to the live
MySkillsFuture search-results endpoint.

The seeded URLs used the legacy
``.../course-directory.html?keyword=<slug>`` format, which the MySkillsFuture
site now redirects to the generic ``courses.myskillsfuture.gov.sg/search``
page, dropping the keyword. This rewrites every entry to
``https://courses.myskillsfuture.gov.sg/search?q=<skill>`` keyed by the skill
name (the JSON key), so each link lands on that skill's course results.

The original .research workbooks are no longer present, so we patch the JSON
directly instead of re-running build_swda_seed.py.

Run:  python scripts/fix_course_urls.py
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
COURSES = ROOT / "app" / "data" / "courses.json"


def main() -> None:
    with open(COURSES, encoding="utf-8") as f:
        courses = json.load(f)

    changed = 0
    for skill, entry in courses.items():
        new_url = f"https://courses.myskillsfuture.gov.sg/search?q={quote_plus(skill)}"
        if entry.get("url") != new_url:
            entry["url"] = new_url
            changed += 1

    with open(COURSES, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"Rewrote {changed}/{len(courses)} course URLs in {COURSES.name}")


if __name__ == "__main__":
    main()
