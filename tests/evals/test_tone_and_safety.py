from sgc_governance.prompt_registry.defaults import SYSTEM_PROMPT_V1, TONE_BLOCKLIST


def test_system_prompt_requires_tool_grounding():
    assert "tool" in SYSTEM_PROMPT_V1.lower() or "Never invent" in SYSTEM_PROMPT_V1


def test_system_prompt_friendly_tone():
    lowered = SYSTEM_PROMPT_V1.lower()
    assert "respectful" in lowered or "friendly" in lowered


def test_no_aggressive_upselling_in_blocklist():
    assert any("purchase" in w or "buy" in w for w in TONE_BLOCKLIST)


def test_rsa_safety_in_triage():
    from sgc_domain.triage_engine import TriageEngine
    engine = TriageEngine()
    result = engine.triage("smoke from engine on highway", [])
    assert result.severity_level == "High"
    assert "hazard" in result.safety_prompt.lower() or result.requires_human_review
