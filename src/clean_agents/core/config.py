"""Configuration management with hierarchy: CLI > env > project > user > defaults."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "anthropic"
    model: str = "claude-opus-4-6"
    api_key: str | None = None
    base_url: str | None = None

    def resolve_api_key(self) -> str:
        """Resolve API key from config or environment."""
        if self.api_key:
            return self.api_key
        env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
        }
        env_var = env_map.get(self.provider, "ANTHROPIC_API_KEY")
        key = os.environ.get(env_var, "")
        if not key:
            raise ValueError(
                f"No API key found. Set {env_var} environment variable or pass --api-key."
            )
        return key


class Config(BaseModel):
    """CLean-agents project configuration."""

    # Project
    project_name: str = "my-agent-system"
    language: str = "en"
    output_dir: str = "./outputs"

    # LLM
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Feature flags
    live_research: bool = True
    auto_open_browser: bool = True
    rich_output: bool = True

    # Paths
    project_dir: str = ".clean-agents"

    def project_path(self) -> Path:
        return Path(self.project_dir)

    def blueprint_path(self) -> Path:
        return self.project_path() / "blueprint.yaml"

    def agents_dir(self) -> Path:
        return self.project_path() / "agents"

    def prompts_dir(self) -> Path:
        return self.project_path() / "prompts"

    def evals_dir(self) -> Path:
        return self.project_path() / "evals"

    def security_dir(self) -> Path:
        return self.project_path() / "security"

    def compliance_dir(self) -> Path:
        return self.project_path() / "compliance"

    def outputs_path(self) -> Path:
        return Path(self.output_dir)

    def history_dir(self) -> Path:
        return self.project_path() / "history"

    def save(self, path: Path | None = None) -> None:
        target = path or (self.project_path() / "config.yaml")
        target.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        with open(target, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def load(cls, path: Path) -> Config:
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)

    @classmethod
    def discover(cls, start_dir: Path | None = None) -> Config:
        """Walk up directories to find .clean-agents/config.yaml."""
        search = start_dir or Path.cwd()
        for parent in [search, *search.parents]:
            config_path = parent / ".clean-agents" / "config.yaml"
            if config_path.exists():
                cfg = cls.load(config_path)
                cfg.project_dir = str(parent / ".clean-agents")
                return cfg
        # Check user config
        user_config = Path.home() / ".config" / "clean-agents" / "config.yaml"
        if user_config.exists():
            return cls.load(user_config)
        return cls()
