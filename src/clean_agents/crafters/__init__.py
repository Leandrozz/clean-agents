"""CLean-agents crafters — design Skills, MCPs, Tools, and Plugins."""

from clean_agents.crafters.base import ArtifactRef, ArtifactSpec, ArtifactType
from clean_agents.crafters.session import (
    Bundle,
    DesignConfig,
    DesignSession,
    Phase,
    Recommendation,
)
from clean_agents.crafters.skill.validators import register_builtin as _reg_skill
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationFinding,
    ValidationReport,
    ValidatorBase,
    ValidatorRegistry,
    get_registry,
)

__all__ = [
    "ArtifactRef",
    "ArtifactSpec",
    "ArtifactType",
    "Bundle",
    "DesignConfig",
    "DesignSession",
    "Level",
    "Phase",
    "Recommendation",
    "Severity",
    "ValidationFinding",
    "ValidationReport",
    "ValidatorBase",
    "ValidatorRegistry",
    "get_registry",
]

# Register built-in skill validators on the global registry at import time.
_reg_skill(get_registry())
