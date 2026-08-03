"""Unit tests for narrative grounding and JD-title cleaning.

Regression guard for the bug where the offline fallback narrative dumped the raw
JD title ("...Skills: Apache Spark...") and filled strengths with generic
"diverse transferable skills", so it read as if the candidate had skills their
full profile does not contain. The narrative must reference only real skills
(matched ones, or the candidate's own profile skills) and a clean role title.
No pipeline/model init needed: both helpers are static.
"""

from app.pipeline.narrative import NarrativeGenerator
from app.pipeline.orchestrator import PipelineOrchestrator

CANDIDATE = {
    "name": "Meera Goh",
    "title": "Senior Engineer",
    "sector": "engineering",
    "years_experience": 9,
    "skills": [
        "Building Information Modelling Application",
        "Cost Management",
        "Project Risk Management",
    ],
}


def test_fallback_uses_real_skills_when_no_match():
    """With no matched skills, the fallback cites the candidate's actual skills."""
    text = NarrativeGenerator._fallback_narrative(
        CANDIDATE, {"title": "Senior Data Engineer"}, {"matched": [], "gap": []}
    )
    assert "Cost Management" in text
    # The generic filler that hid the lack of evidence is gone.
    assert "diverse transferable skills" not in text


def test_fallback_uses_matched_skills_when_present():
    """Matched skills and the biggest gap are referenced when available."""
    skills = {"matched": ["Data Governance", "Data Analytics"], "gap": ["System Integration"]}
    text = NarrativeGenerator._fallback_narrative(
        CANDIDATE, {"title": "Senior Data Engineer"}, skills
    )
    assert "Data Governance" in text
    assert "System Integration" in text


def test_fallback_does_not_leak_jd_skills_list():
    """The narrative never dumps the JD's 'Skills:' list as the candidate's."""
    text = NarrativeGenerator._fallback_narrative(
        CANDIDATE, {"title": "Senior Data Engineer"}, {"matched": [], "gap": []}
    )
    assert "Skills:" not in text
    assert "Apache" not in text


def test_extract_jd_title_strips_skills_list():
    """The title used in the narrative drops the inline 'Skills:' dump."""
    title = PipelineOrchestrator._extract_jd_title(
        "Senior Data Engineer: Build petabyte-scale data pipelines. "
        "Skills: Apache Spark, Python, SQL."
    )
    # Trailing period is stripped so the narrative's own full-stop doesn't double.
    assert title == "Senior Data Engineer: Build petabyte-scale data pipelines"


def test_extract_jd_title_plain_title_unchanged():
    """A title with no skills list passes through untouched."""
    assert PipelineOrchestrator._extract_jd_title("Senior Data Engineer") == "Senior Data Engineer"
