"""AI-enhanced helpers wrapping ClaudeArchitect for the Skills vertical."""

from __future__ import annotations

from typing import Protocol


class AIClient(Protocol):
    """Protocol for AI clients used by Skill validators."""

    def detect_contradictions(self, text: str) -> list[str]:
        """Detect logical contradictions in text. Return list of contradiction descriptions."""

    def suggest_triggers(self, description: str) -> list[str]:
        """Suggest trigger keywords for a skill description."""

    def generate_eval_prompts(
        self, description: str, triggers: list[str], n: int
    ) -> dict[str, list[str]]:
        """Generate evaluation prompts for a skill with given description and triggers."""
