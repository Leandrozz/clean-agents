from clean_agents.crafters.knowledge import (
    AntiPattern,
    BestPractice,
    KnowledgeBase,
)


def test_best_practice_model():
    bp = BestPractice(
        id="progressive-disclosure",
        title="Use progressive disclosure",
        body="Keep SKILL.md concise; move detail to references/.",
        applies_to=["skill"],
    )
    assert bp.id == "progressive-disclosure"


def test_anti_pattern_model():
    ap = AntiPattern(
        id="hardcoded-stats",
        title="Hard-coded statistics",
        body="Exact percentages age poorly.",
        rule_id="SKILL-L2-HARDCODED-STATS",
        applies_to=["skill"],
    )
    assert ap.rule_id == "SKILL-L2-HARDCODED-STATS"


def test_knowledge_base_is_abc():
    import inspect
    assert inspect.isabstract(KnowledgeBase)


from pathlib import Path


def test_yaml_knowledge_loads_seeded_files():
    from clean_agents.crafters.skill.knowledge import SkillKnowledge
    kb = SkillKnowledge(root=Path("knowledge/crafters/skill"))
    bps = kb.get_best_practices("skill")
    aps = kb.get_anti_patterns("skill")
    assert any(bp.id == "progressive-disclosure" for bp in bps)
    assert any(ap.rule_id == "SKILL-L2-HARDCODED-STATS" for ap in aps)
