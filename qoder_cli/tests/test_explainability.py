"""Unit tests for explainability engine (data-driven: uses real SWDA skills)."""


def test_explainability_matched_gap():
    """Explainability correctly identifies matched and gap skills."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    jd_skills = ["Business Planning", "Data Governance", "Regulatory Compliance", "Collateral Management"]
    cand_skills = ["Business Planning", "Data Governance", "Ethical Culture", "Quality Assurance"]

    result = engine.run(jd_skills, cand_skills)
    assert "Business Planning" in result["matched"]
    assert "Data Governance" in result["matched"]
    assert "Regulatory Compliance" in result["gap"]
    assert "Collateral Management" in result["gap"]


def test_explainability_bridge():
    """Explainability identifies bridge skills from derived bridges.json."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    # "Business Continuity Management" is bridged via "Business Continuity Planning"
    jd_skills = ["Business Continuity Management"]
    cand_skills = ["Business Continuity Planning", "Quality Assurance"]

    result = engine.run(jd_skills, cand_skills)
    assert "Business Continuity Management" in result["gap"]
    bridge_skills = [b["gap_skill"] for b in result["bridge"]]
    assert "Business Continuity Management" in bridge_skills
    # Verify bridge metadata
    b = result["bridge"][0]
    assert b["via_skill"] == "Business Continuity Planning"
    assert 0.0 < b["confidence"] <= 1.0


def test_explainability_no_bridge_when_no_via():
    """No bridge if candidate lacks the bridging skill."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    # "Business Continuity Management" bridges via "Business Continuity Planning"
    # but candidate does NOT have that skill
    jd_skills = ["Business Continuity Management"]
    cand_skills = ["Ethical Culture", "Quality Assurance"]

    result = engine.run(jd_skills, cand_skills)
    assert "Business Continuity Management" in result["gap"]
    assert len(result["bridge"]) == 0


def test_extract_skills():
    """Skill extraction finds known SWDA skills in text."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    text = (
        "We need someone with Business Planning and Data Governance experience, "
        "plus Regulatory Compliance and Quality Assurance in financial services."
    )
    skills = engine.extract_skills(text)
    assert "Business Planning" in skills
    assert "Data Governance" in skills
    assert "Regulatory Compliance" in skills
    assert "Quality Assurance" in skills


def test_explainability_returns_correct_structure():
    """Result has matched, gap, bridge, matched_detail, and proficiency_fit keys."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    result = engine.run(["Business Planning"], ["Business Planning"])
    assert "matched" in result
    assert "gap" in result
    assert "bridge" in result
    assert "matched_detail" in result
    assert "proficiency_fit" in result


def test_proficiency_fit_full_credit():
    """Proficiency fit is 1.0 when candidate meets all required levels."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    jd_skills = ["Business Planning", "Data Governance"]
    cand_skills = ["Business Planning", "Data Governance"]
    required = {"Business Planning": 3, "Data Governance": 2}
    candidate = {"Business Planning": 4, "Data Governance": 3}

    result = engine.run(jd_skills, cand_skills, required, candidate)
    assert result["proficiency_fit"] == 1.0
    for detail in result["matched_detail"]:
        assert detail["met"] is True


def test_proficiency_fit_partial_credit():
    """Proficiency fit gives partial credit when candidate is below required PL."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    jd_skills = ["Financial Statements Review"]  # required PL 4 in jd_001
    cand_skills = ["Financial Statements Review"]
    required = {"Financial Statements Review": 4}
    candidate = {"Financial Statements Review": 2}  # below required

    result = engine.run(jd_skills, cand_skills, required, candidate)
    assert result["proficiency_fit"] == 0.5  # 2/4
    assert result["matched_detail"][0]["met"] is False


def test_proficiency_fit_none_without_levels():
    """Proficiency fit is None when no required levels are provided."""
    from app.pipeline.explainability import ExplainabilityEngine

    engine = ExplainabilityEngine()
    result = engine.run(["Business Planning"], ["Business Planning"])
    assert result["proficiency_fit"] is None
