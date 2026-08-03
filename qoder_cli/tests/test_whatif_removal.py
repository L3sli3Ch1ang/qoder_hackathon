"""Unit tests for What-If skill removal (PipelineOrchestrator._remove_skill_mentions).

The helper is a static method that only reads the skill taxonomy — no models,
no Qdrant, no orchestrator instance needed. Skill names are picked from the
real taxonomy (data-driven, per repo convention).
"""

import pytest

from app.data import get_all_skills
from app.pipeline.orchestrator import PipelineOrchestrator

remove = PipelineOrchestrator._remove_skill_mentions


@pytest.fixture(scope="module")
def substring_pair() -> tuple[str, str]:
    """A real (shorter, longer) taxonomy pair where shorter ⊂ longer."""
    skills = sorted(get_all_skills())
    for shorter in skills:
        for longer in skills:
            if shorter != longer and shorter.lower() in longer.lower():
                return shorter, longer
    pytest.fail("taxonomy has no substring skill pair")


def test_removes_standalone_mention_case_insensitively(substring_pair):
    shorter, _ = substring_pair
    text = f"Requires {shorter.lower()} and general aptitude."
    result = remove(text, shorter)
    assert shorter.lower() not in result.lower()
    assert "general aptitude" in result


def test_preserves_longer_distinct_skill_title(substring_pair):
    shorter, longer = substring_pair
    text = f"Deep {longer} expertise required."
    result = remove(text, shorter)
    assert longer in result


def test_removes_standalone_but_keeps_longer_when_both_present(substring_pair):
    shorter, longer = substring_pair
    text = f"Needs {shorter} plus {longer.lower()} experience."
    result = remove(text, shorter)
    assert longer.lower() in result.lower()
    assert result.lower().count(shorter.lower()) == 1  # only inside longer


def test_does_not_clip_mid_word(substring_pair):
    shorter, _ = substring_pair
    text = f"Pseudo-skill {shorter}x should survive."
    result = remove(text, shorter)
    assert f"{shorter}x" in result


def test_regex_metacharacters_in_skill_are_escaped():
    result = remove("Knows C++ well.", "C++")
    assert "C++" not in result
    assert "well" in result
