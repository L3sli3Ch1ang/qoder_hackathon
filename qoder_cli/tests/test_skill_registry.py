"""Tests for the SWDA-derived skill registry and derived bridges."""


def test_registry_non_empty():
    """Skill registry loads and is non-empty."""
    from app.data import get_skill_registry

    registry = get_skill_registry()
    assert isinstance(registry, dict)
    assert len(registry) > 100  # 434 skills generated


def test_registry_entry_structure():
    """Each registry entry has required fields with correct types."""
    from app.data import get_skill_registry

    registry = get_skill_registry()
    for skill, entry in list(registry.items())[:20]:
        assert entry["type"] in ("tsc", "ccs"), f"{skill}: bad type"
        assert isinstance(entry["description"], str), f"{skill}: description not str"
        assert isinstance(entry["sectors"], list), f"{skill}: sectors not list"
        assert isinstance(entry["emerging"], bool), f"{skill}: emerging not bool"
        assert isinstance(entry["casl"], bool), f"{skill}: casl not bool"


def test_registry_proficiency_descriptions():
    """Registry entries carry per-level proficiency descriptions."""
    from app.data import get_skill_registry

    registry = get_skill_registry()
    # At least some entries should have proficiency descriptions
    with_pl = [e for e in registry.values() if e.get("proficiency_descriptions")]
    assert len(with_pl) > 50, "expected many skills with proficiency descriptions"
    # Check structure of one
    sample = with_pl[0]
    for level, desc in sample["proficiency_descriptions"].items():
        assert level in ("1", "2", "3", "4", "5", "6")
        assert isinstance(desc, str) and desc


def test_registry_has_emerging_and_casl():
    """Registry contains skills flagged as Emerging and CASL."""
    from app.data import get_skill_registry

    registry = get_skill_registry()
    emerging = [s for s, e in registry.items() if e["emerging"]]
    casl = [s for s, e in registry.items() if e["casl"]]
    assert len(emerging) > 0, "expected at least one Emerging skill"
    assert len(casl) > 0, "expected at least one CASL skill"


def test_bridges_derived_correctly():
    """Bridges are derived: via != key, confidence in [0, 1]."""
    from app.data import get_bridges

    bridges = get_bridges()
    assert len(bridges) >= 30, f"expected >=30 bridges, got {len(bridges)}"
    for gap_skill, info in bridges.items():
        assert info["via"] != gap_skill, f"{gap_skill}: via must differ from key"
        assert 0.0 < info["confidence"] <= 1.0, (
            f"{gap_skill}: confidence {info['confidence']} out of range"
        )


def test_bridges_via_skills_in_registry():
    """Every bridge 'via' skill exists in the registry."""
    from app.data import get_bridges, get_skill_registry

    registry = get_skill_registry()
    bridges = get_bridges()
    for gap_skill, info in bridges.items():
        assert info["via"] in registry, (
            f"bridge via '{info['via']}' not in registry"
        )


def test_taxonomy_skills_in_registry():
    """Every skill in the taxonomy exists in the registry."""
    from app.data import get_skill_registry, get_skill_taxonomy

    registry = get_skill_registry()
    taxonomy = get_skill_taxonomy()
    for sector, skills in taxonomy.items():
        for skill in skills:
            assert skill in registry, (
                f"taxonomy skill '{skill}' (sector={sector}) not in registry"
            )
