"""Concrete FlatYAMLKnowledge impl for the Skills vertical."""

from __future__ import annotations

from pathlib import Path

import yaml

from clean_agents.crafters.base import ArtifactRef, ArtifactType
from clean_agents.crafters.knowledge import (
    AntiPattern,
    BestPractice,
    JinjaTemplate,
    KnowledgeBase,
)


class SkillKnowledge(KnowledgeBase):
    def __init__(self, root: Path) -> None:
        self.root = root

    def _load_yaml(self, name: str) -> list[dict]:
        path = self.root / name
        if not path.exists():
            return []
        return list(yaml.safe_load(path.read_text(encoding="utf-8")) or [])

    def get_best_practices(self, artifact_type: str | None = None) -> list[BestPractice]:
        rows = self._load_yaml("best-practices.yaml")
        out = [BestPractice.model_validate(r) for r in rows]
        if artifact_type:
            out = [b for b in out if artifact_type in b.applies_to]
        return out

    def get_anti_patterns(self, artifact_type: str | None = None) -> list[AntiPattern]:
        rows = self._load_yaml("anti-patterns.yaml")
        out = [AntiPattern.model_validate(r) for r in rows]
        if artifact_type:
            out = [a for a in out if artifact_type in a.applies_to]
        return out

    def get_similar(self, description: str, k: int = 5) -> list[ArtifactRef]:
        # Scan ~/.claude/skills/* for similar descriptions via TF-IDF (MiniLM opt-in).
        # Implementation detail: use extract_keywords overlap; upgrade in M10.2.
        from clean_agents.crafters.validators.collision import (
            default_installed_roots,
        )
        from clean_agents.crafters.validators.semantic import extract_keywords

        refs: list[ArtifactRef] = []
        own_keys = set(extract_keywords(description))
        for root in default_installed_roots():
            if not root.exists():
                continue
            for skill_dir in root.iterdir():
                if not skill_dir.is_dir():
                    continue
                readme = skill_dir / "SKILL.md"
                if not readme.exists():
                    continue
                overlap = own_keys & set(
                    extract_keywords(
                        readme.read_text(encoding="utf-8", errors="ignore")
                    )
                )
                if overlap:
                    refs.append(
                        ArtifactRef(
                            artifact_type=ArtifactType.SKILL,
                            name=skill_dir.name,
                            rationale=f"keyword overlap: {sorted(overlap)[:5]}",
                            spec_path=skill_dir / ".skill-spec.yaml",
                            status="installed",
                        )
                    )
        refs.sort(key=lambda r: len(r.rationale), reverse=True)
        return refs[:k]

    def get_template(self, name: str) -> JinjaTemplate:
        tpl = self.root / "templates" / name
        if not tpl.exists():
            raise FileNotFoundError(f"template not found: {name}")
        return JinjaTemplate(name=name, path=tpl)
