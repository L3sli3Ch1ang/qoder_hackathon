"""Guard that every curated sample JD exercises the explainability engine.

Regression guard for the bug where the "Senior Data Engineer" / "IoT Data
Engineer" samples listed only tool names (Apache Spark, Python, SQL, Airflow,
Data Warehousing, Cloud Computing) that are absent from the SWDA taxonomy.
``extract_skills`` then returned nothing, collapsing the matched/gap/proficiency
breakdown into "Matched 0 / Gaps 0 - no gaps - perfect fit" and falling back to
semantic-only ranking (a zero-match candidate floated to the top).

Single source of truth: the JD texts are read straight out of
``templates/index.html`` so this test cannot drift from what the UI sends.
"""

import re
from pathlib import Path

from app.pipeline.explainability import ExplainabilityEngine

INDEX_HTML = Path(__file__).resolve().parent.parent / "templates" / "index.html"


def _sample_jds() -> list[str]:
    """Extract the non-empty sample-JD option values from the UI template."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    # Isolate the sample-JD <select id="sample-jd"> block so the sector/score
    # filter <option>s elsewhere on the page are not captured.
    block = re.search(r'<select id="sample-jd".*?</select>', html, flags=re.DOTALL)
    assert block, "sample-jd select not found in templates/index.html"
    # Drop the empty placeholder (value=""); keep only real JD texts.
    return [v for v in re.findall(r'<option value="([^"]*)">', block.group(0)) if v.strip()]


def test_sample_jds_exist():
    """The five curated sample JDs are all present."""
    jds = _sample_jds()
    assert len(jds) >= 5, f"expected the 5 curated sample JDs, found {len(jds)}"


def test_each_sample_jd_yields_framework_skills():
    """Every sample JD contains enough SWDA skills for a meaningful breakdown."""
    engine = ExplainabilityEngine()
    for jd in _sample_jds():
        skills = engine.extract_skills(jd)
        assert len(skills) >= 3, (
            f"sample JD recognizes too few framework skills ({len(skills)}): {jd!r}"
        )
