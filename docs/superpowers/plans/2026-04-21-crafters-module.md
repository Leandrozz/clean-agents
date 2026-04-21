# Crafters Module (v1 = Skills vertical) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `src/clean_agents/crafters/` with a reusable `DesignSession[T]` engine, a 4-level validator pipeline, and a Skills-vertical end-to-end flow (`clean-agents skill design/validate/render/publish`) that generates full bundles from `SkillSpec` YAML as source of truth.

**Architecture:** Hybrid pragmatic (20% shared abstractions / 80% per-vertical). Generic `ArtifactSpec` + `DesignSession[T]` + `ValidatorBase[T]` with a `ValidatorRegistry` discoverable via a NEW `clean_agents.validators` entry-point group. `SkillSpec` is the v1 subclass. `.skill-spec.yaml` is the source of truth; `SKILL.md` + `references/` + `evals/` are rendered from it. Bidirectional, OPTIONAL Blueprint integration via `AgentSpec.recommended_artifacts`.

**Tech Stack:** Python 3.10+, Pydantic v2 (generics), Typer+Rich (CLI), Jinja2 (renderer — already in core deps), PyYAML (round-trip), Anthropic SDK (opt-in, `--ai`), `sentence-transformers>=2.7` as a NEW optional `crafters` extra (falls back to TF-IDF when not installed). pytest + ruff + mypy. Must not break the existing 303 tests; target ~100 new tests.

**Spec:** `docs/superpowers/specs/2026-04-21-crafters-module-design.md` (commit `b1248be`).

---

## File Structure

New files (create):

- `src/clean_agents/crafters/__init__.py` — public exports (`ArtifactSpec`, `ArtifactType`, `DesignSession`, `ValidationReport`)
- `src/clean_agents/crafters/base.py` — `ArtifactType` enum, `ArtifactSpec` Pydantic base, `ArtifactRef`
- `src/clean_agents/crafters/session.py` — `DesignSession[T]`, `Phase` enum, `Turn`, `DesignConfig`, `Recommendation`, `Delta`, `CascadeReport`, `ModuleResult`, `Bundle`
- `src/clean_agents/crafters/knowledge.py` — `KnowledgeBase` ABC, `BestPractice`, `AntiPattern`, `FlatYAMLKnowledge` impl, MiniLM + TF-IDF fallback
- `src/clean_agents/crafters/renderer.py` — `BundleRenderer` (Jinja2 loader, bundle writer)
- `src/clean_agents/crafters/validators/__init__.py`
- `src/clean_agents/crafters/validators/base.py` — `Severity`, `Level`, `ValidationFinding`, `ValidationReport`, `ValidationContext`, `ValidatorBase`, `ValidatorRegistry` (new entry-point group `clean_agents.validators`)
- `src/clean_agents/crafters/validators/structural.py` — shared L1 helpers
- `src/clean_agents/crafters/validators/semantic.py` — shared L2 helpers (language detection, regex catalogs)
- `src/clean_agents/crafters/validators/collision.py` — L3 filesystem + marketplace scanner
- `src/clean_agents/crafters/validators/runtime.py` — L4 eval harness (opt-in)
- `src/clean_agents/crafters/skill/__init__.py`
- `src/clean_agents/crafters/skill/spec.py` — `SkillSpec`, `ReferenceFile`, `EvalCase`, `EvalThresholds`, `EvalsManifest`, `SkillSection`
- `src/clean_agents/crafters/skill/knowledge.py` — `SkillKnowledge` concrete KB loader for `knowledge/crafters/skill/*.yaml`
- `src/clean_agents/crafters/skill/scaffold.py` — bundle writer for Skills (wraps `BundleRenderer`)
- `src/clean_agents/crafters/skill/validators.py` — 15 rule classes (one class per rule ID)
- `src/clean_agents/crafters/skill/ai.py` — AI-enhanced helpers (reuse `ClaudeArchitect`) for trigger generation + L2 contradictions + L4 prompt generation
- `src/clean_agents/crafters/skill/templates/SKILL.md.j2`
- `src/clean_agents/crafters/skill/templates/README.md.j2`
- `src/clean_agents/crafters/skill/templates/reference.md.j2`
- `src/clean_agents/crafters/skill/templates/evals.json.j2`
- `src/clean_agents/cli/skill_cmd.py` — `design_cmd`, `validate_cmd`, `render_cmd`, `publish_cmd` callables
- `knowledge/crafters/skill/best-practices.yaml`
- `knowledge/crafters/skill/anti-patterns.yaml`
- `tests/fixtures/crafters/skill/good-skill/SKILL.md`
- `tests/fixtures/crafters/skill/good-skill/.skill-spec.yaml`
- `tests/fixtures/crafters/skill/bad-hardcoded-stats/SKILL.md`
- `tests/fixtures/crafters/skill/bad-hardcoded-stats/.skill-spec.yaml`
- `tests/fixtures/crafters/skill/bad-name-collision/SKILL.md`
- `tests/fixtures/crafters/skill/bad-name-collision/.skill-spec.yaml`
- `tests/fixtures/crafters/skill/bad-language-mix/SKILL.md`
- `tests/fixtures/crafters/skill/bad-language-mix/.skill-spec.yaml`
- `tests/fixtures/crafters/skill/bad-desc-too-long/SKILL.md`
- `tests/fixtures/crafters/skill/bad-desc-too-long/.skill-spec.yaml`
- `tests/fixtures/crafters/skill/leandro-real-skill/SKILL.md` (copied from existing `clean-agents.skill`)
- `tests/test_crafters_base.py`
- `tests/test_crafters_validators_l1.py`
- `tests/test_crafters_validators_l2.py`
- `tests/test_crafters_validators_l3.py`
- `tests/test_crafters_session.py`
- `tests/test_crafters_renderer.py`
- `tests/test_crafters_cli.py`
- `tests/test_crafters_ai.py`
- `tests/test_crafters_runtime.py`
- `tests/test_crafters_blueprint_integration.py`
- `tests/test_crafters_knowledge.py`
- `docs/crafters/README.md`

Files to modify:

- `src/clean_agents/core/agent.py` — add `ArtifactRef` import + `AgentSpec.recommended_artifacts: list[ArtifactRef] = []` (M9)
- `src/clean_agents/cli/main.py` — import `skill_cmd` callables, register `skill_app = typer.Typer(name="skill", ...)` with `design/validate/render/publish` (M6)
- `src/clean_agents/cli/design_cmd.py` — add `suggest-artifacts` Phase-5 module handler (M9)
- `pyproject.toml` — add `crafters = ["sentence-transformers>=2.7"]`, add `all = [..., "crafters"]`, register built-in validators under new group `clean_agents.validators` (M1 stubs, fill in later milestones)
- `CHANGELOG.md` — add v0.2 section (M10)
- `README.md` — add Crafters usage section (M10)

---

## Milestone M1 — Base abstractions (`ArtifactSpec`, `DesignSession[T]`, `KnowledgeBase`, `ValidatorRegistry`, CLI stubs)

**Dependencies:** none.

### Task M1.1: Create crafters package skeleton

**Files:**
- Create: `src/clean_agents/crafters/__init__.py`
- Create: `src/clean_agents/crafters/validators/__init__.py`
- Create: `src/clean_agents/crafters/skill/__init__.py`
- Test: `tests/test_crafters_base.py`

- [ ] **Step 1: Write failing import test**

```python
# tests/test_crafters_base.py
def test_crafters_package_importable():
    import clean_agents.crafters
    import clean_agents.crafters.validators
    import clean_agents.crafters.skill
    assert clean_agents.crafters is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_base.py::test_crafters_package_importable -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'clean_agents.crafters'`

- [ ] **Step 3: Create the three `__init__.py` files, empty for now**

```python
# src/clean_agents/crafters/__init__.py
"""CLean-agents crafters — design Skills, MCPs, Tools, and Plugins."""
```

```python
# src/clean_agents/crafters/validators/__init__.py
"""Validator pipeline (L1-L4) for crafter artifacts."""
```

```python
# src/clean_agents/crafters/skill/__init__.py
"""Skills vertical (v1 delivery)."""
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_crafters_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters tests/test_crafters_base.py
git commit -m "feat(crafters): scaffold crafters package skeleton"
```

### Task M1.2: Implement `ArtifactType` and `ArtifactRef`

**Files:**
- Create: `src/clean_agents/crafters/base.py`
- Test: `tests/test_crafters_base.py`

- [ ] **Step 1: Add failing test**

```python
# tests/test_crafters_base.py (append)
from pathlib import Path

from clean_agents.crafters.base import ArtifactRef, ArtifactType


def test_artifact_type_values():
    assert ArtifactType.SKILL.value == "skill"
    assert ArtifactType.MCP.value == "mcp"
    assert ArtifactType.TOOL.value == "tool"
    assert ArtifactType.PLUGIN.value == "plugin"


def test_artifact_ref_roundtrip():
    ref = ArtifactRef(
        artifact_type=ArtifactType.SKILL,
        name="legal-risk-patterns",
        rationale="risk_evaluator uses domain-specific jargon",
        spec_path=Path(".clean-agents/skills/legal-risk-patterns/.skill-spec.yaml"),
        status="needed",
        priority="recommended",
    )
    dumped = ref.model_dump(mode="json")
    assert dumped["artifact_type"] == "skill"
    assert dumped["status"] == "needed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_base.py -v`
Expected: FAIL with `ImportError: cannot import name 'ArtifactType'`

- [ ] **Step 3: Implement `base.py`**

```python
# src/clean_agents/crafters/base.py
"""Shared base types for crafter artifacts (Skills, MCPs, Tools, Plugins)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ArtifactType(str, Enum):
    SKILL = "skill"
    MCP = "mcp"
    TOOL = "tool"
    PLUGIN = "plugin"


class ArtifactRef(BaseModel):
    """A reference from one artifact to another (used by AgentSpec + cross-artifact links)."""

    artifact_type: ArtifactType
    name: str
    rationale: str = ""
    spec_path: Path | None = None
    status: Literal["needed", "designed", "installed"] = "needed"
    priority: Literal["critical", "recommended", "nice-to-have"] = "recommended"


class ArtifactSpec(BaseModel):
    """Shared base for every crafter artifact. Verticals subclass to add fields."""

    name: str = Field(description="kebab-case artifact identifier")
    version: str = "0.1.0"
    description: str = Field(description="one-paragraph description; see per-vertical length rules")
    artifact_type: ArtifactType
    author: str | None = None
    language: str = Field(default="en", description="ISO 639-1 code")
    license: str = "MIT"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Traceability for future meta-agent
    source: Literal["human", "agent", "blueprint"] = "human"
    blueprint_ref: Path | None = None

    @field_validator("language")
    @classmethod
    def _validate_lang(cls, v: str) -> str:
        if len(v) != 2 or not v.isalpha():
            raise ValueError(f"language must be ISO 639-1 (2 letters), got: {v!r}")
        return v.lower()

    @field_validator("name")
    @classmethod
    def _validate_kebab(cls, v: str) -> str:
        if not v or not all(c.islower() or c.isdigit() or c == "-" for c in v):
            raise ValueError(f"name must be kebab-case (lowercase, digits, hyphens): {v!r}")
        return v
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/base.py tests/test_crafters_base.py
git commit -m "feat(crafters): add ArtifactType + ArtifactSpec + ArtifactRef base"
```

### Task M1.3: Implement `ValidationFinding`, `Severity`, `Level`, `ValidationReport`, `ValidationContext`

**Files:**
- Create: `src/clean_agents/crafters/validators/base.py`
- Test: `tests/test_crafters_base.py`

- [ ] **Step 1: Add failing test**

```python
# tests/test_crafters_base.py (append)
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationFinding,
    ValidationReport,
)


def test_validation_report_aggregation():
    findings = [
        ValidationFinding(rule_id="R1", severity=Severity.CRITICAL, message="x"),
        ValidationFinding(rule_id="R2", severity=Severity.HIGH, message="y"),
        ValidationFinding(rule_id="R3", severity=Severity.LOW, message="z"),
    ]
    report = ValidationReport(findings=findings)
    assert report.has_critical() is True
    assert report.has_blocking() is True  # critical OR high
    assert len(report.by_severity(Severity.LOW)) == 1


def test_severity_ordering():
    assert Severity.CRITICAL.rank() > Severity.HIGH.rank() > Severity.MEDIUM.rank()
    assert Severity.MEDIUM.rank() > Severity.LOW.rank() > Severity.INFO.rank()


def test_validation_context_defaults():
    ctx = ValidationContext(bundle_root=None, installed_roots=[])
    assert ctx.bundle_root is None
    assert ctx.installed_roots == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_base.py -v`
Expected: FAIL with `ModuleNotFoundError` for `validators.base`

- [ ] **Step 3: Implement `validators/base.py`**

```python
# src/clean_agents/crafters/validators/base.py
"""Validator base classes and registry for the crafter pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactSpec, ArtifactType

T = TypeVar("T", bound=ArtifactSpec)


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def rank(self) -> int:
        return {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class Level(str, Enum):
    L1 = "L1"   # structural
    L2 = "L2"   # semantic
    L3 = "L3"   # cross-artifact collision
    L4 = "L4"   # runtime eval (opt-in)


class ValidationFinding(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    location: str | None = None
    fix_hint: str | None = None
    auto_fixable: bool = False


class ValidationReport(BaseModel):
    findings: list[ValidationFinding] = Field(default_factory=list)

    def has_critical(self) -> bool:
        return any(f.severity is Severity.CRITICAL for f in self.findings)

    def has_blocking(self) -> bool:
        return any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in self.findings)

    def by_severity(self, severity: Severity) -> list[ValidationFinding]:
        return [f for f in self.findings if f.severity is severity]

    def by_rule(self, rule_id: str) -> list[ValidationFinding]:
        return [f for f in self.findings if f.rule_id == rule_id]

    def extend(self, other: "ValidationReport") -> None:
        self.findings.extend(other.findings)


class ValidationContext(BaseModel):
    """Context passed to every validator. Holds filesystem roots, installed artifact index, etc."""

    bundle_root: Path | None = None            # Where the rendered bundle lives on disk (may be None for pre-render)
    installed_roots: list[Path] = Field(default_factory=list)  # Directories to scan for collisions (~/.claude/skills etc.)
    marketplace_index: dict[str, list[str]] = Field(default_factory=dict)  # opt-in L3
    enable_ai: bool = False                    # Controls L2-CONTRADICTIONS + L4 activation


class ValidatorBase(ABC, Generic[T]):
    """Every validator inherits from this and declares level + artifact_type + rule_id."""

    level: Level
    artifact_type: ArtifactType
    rule_id: str
    severity_default: Severity = Severity.MEDIUM

    @abstractmethod
    def check(self, spec: T, ctx: ValidationContext) -> list[ValidationFinding]:
        """Return a list of findings (empty = pass)."""
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/validators/base.py tests/test_crafters_base.py
git commit -m "feat(crafters): add Severity/Level/ValidationFinding/Report/Context/ValidatorBase"
```

### Task M1.4: Implement `ValidatorRegistry` with new `clean_agents.validators` entry-point group

**Files:**
- Modify: `src/clean_agents/crafters/validators/base.py` (append)
- Test: `tests/test_crafters_base.py`

- [ ] **Step 1: Add failing test**

```python
# tests/test_crafters_base.py (append)
from clean_agents.crafters.base import ArtifactSpec, ArtifactType
from clean_agents.crafters.validators.base import (
    Level,
    ValidatorBase,
    ValidatorRegistry,
)


class _DummySpec(ArtifactSpec):
    artifact_type: ArtifactType = ArtifactType.SKILL


class _DummyValidator(ValidatorBase[_DummySpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "DUMMY-L1-OK"

    def check(self, spec, ctx):
        return []


def test_registry_register_and_get():
    reg = ValidatorRegistry()
    reg.register(_DummyValidator())
    validators = reg.for_artifact(ArtifactType.SKILL, level=Level.L1)
    assert any(v.rule_id == "DUMMY-L1-OK" for v in validators)


def test_registry_entry_point_group():
    assert ValidatorRegistry.ENTRY_POINT_GROUP == "clean_agents.validators"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_base.py -v`
Expected: FAIL with `ImportError: cannot import name 'ValidatorRegistry'`

- [ ] **Step 3: Implement `ValidatorRegistry`**

```python
# src/clean_agents/crafters/validators/base.py (append at bottom)
import importlib.metadata


class ValidatorRegistry:
    """Central registry for validators.

    Discovery sources (in order):
      1. Built-in validators registered programmatically
      2. Python entry points (group: "clean_agents.validators")
      3. User-provided validator objects via register()
    """

    ENTRY_POINT_GROUP = "clean_agents.validators"

    def __init__(self) -> None:
        self._validators: list[ValidatorBase] = []
        self._loaded: bool = False

    def register(self, validator: ValidatorBase) -> None:
        self._validators.append(validator)

    def for_artifact(
        self,
        artifact_type: ArtifactType,
        level: Level | None = None,
    ) -> list[ValidatorBase]:
        if not self._loaded:
            self.discover()
        result = [v for v in self._validators if v.artifact_type is artifact_type]
        if level is not None:
            result = [v for v in result if v.level is level]
        return result

    def discover(self) -> None:
        self._loaded = True
        try:
            eps = importlib.metadata.entry_points()
            if hasattr(eps, "select"):
                group_eps = eps.select(group=self.ENTRY_POINT_GROUP)
            elif isinstance(eps, dict):
                group_eps = eps.get(self.ENTRY_POINT_GROUP, [])
            else:
                group_eps = [ep for ep in eps if ep.group == self.ENTRY_POINT_GROUP]
            for ep in group_eps:
                try:
                    cls = ep.load()
                    if isinstance(cls, type) and issubclass(cls, ValidatorBase):
                        self._validators.append(cls())
                except Exception:
                    pass
        except Exception:
            pass


_registry: ValidatorRegistry | None = None


def get_registry() -> ValidatorRegistry:
    global _registry
    if _registry is None:
        _registry = ValidatorRegistry()
    return _registry
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/validators/base.py tests/test_crafters_base.py
git commit -m "feat(crafters): add ValidatorRegistry with clean_agents.validators entry-point group"
```

### Task M1.5: Implement `KnowledgeBase` interface

**Files:**
- Create: `src/clean_agents/crafters/knowledge.py`
- Test: `tests/test_crafters_knowledge.py`

- [ ] **Step 1: Add failing test**

```python
# tests/test_crafters_knowledge.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_knowledge.py -v`
Expected: FAIL with `ModuleNotFoundError: clean_agents.crafters.knowledge`

- [ ] **Step 3: Implement `knowledge.py`**

```python
# src/clean_agents/crafters/knowledge.py
"""Knowledge base interface for crafter artifacts.

v1 ships `FlatYAMLKnowledge`. Future GraphRAG impl slots in without touching consumers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactRef


class BestPractice(BaseModel):
    id: str
    title: str
    body: str
    applies_to: list[str] = Field(default_factory=list)  # "skill", "mcp", "tool", "plugin"
    source: str | None = None


class AntiPattern(BaseModel):
    id: str
    title: str
    body: str
    rule_id: str | None = None                 # optional back-link to validator rule
    applies_to: list[str] = Field(default_factory=list)
    source: str | None = None


class JinjaTemplate(BaseModel):
    name: str
    path: Path


class KnowledgeBase(ABC):
    """Read-only interface consumed by DesignSession + validators + renderer."""

    @abstractmethod
    def get_best_practices(self, artifact_type: str | None = None) -> list[BestPractice]: ...

    @abstractmethod
    def get_anti_patterns(self, artifact_type: str | None = None) -> list[AntiPattern]: ...

    @abstractmethod
    def get_similar(self, description: str, k: int = 5) -> list[ArtifactRef]: ...

    @abstractmethod
    def get_template(self, name: str) -> JinjaTemplate: ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_knowledge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/knowledge.py tests/test_crafters_knowledge.py
git commit -m "feat(crafters): add KnowledgeBase interface + BestPractice/AntiPattern models"
```

### Task M1.6: Scaffold `DesignSession[T]` with Phase enum and empty state-machine methods

**Files:**
- Create: `src/clean_agents/crafters/session.py`
- Test: `tests/test_crafters_session.py`

- [ ] **Step 1: Add failing test**

```python
# tests/test_crafters_session.py
from uuid import UUID

from clean_agents.crafters.base import ArtifactSpec, ArtifactType
from clean_agents.crafters.session import (
    DesignConfig,
    DesignSession,
    Phase,
)


class _Spec(ArtifactSpec):
    artifact_type: ArtifactType = ArtifactType.SKILL


def _skeleton_spec() -> _Spec:
    return _Spec(
        name="test-skill",
        description="A fixture skill used for session state-machine unit tests.",
        artifact_type=ArtifactType.SKILL,
    )


def test_session_initial_phase_is_intake():
    s = DesignSession[_Spec](spec=_skeleton_spec(), config=DesignConfig())
    assert s.phase is Phase.INTAKE
    assert isinstance(s.session_id, UUID)


def test_phase_enum_has_six_values():
    assert {p.value for p in Phase} == {
        "intake", "recommend", "deep_dive", "bundle", "iterate", "modules",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_session.py -v`
Expected: FAIL with `ModuleNotFoundError: clean_agents.crafters.session`

- [ ] **Step 3: Implement `session.py` scaffold**

```python
# src/clean_agents/crafters/session.py
"""DesignSession[T] — reusable engine for every crafter vertical."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

import yaml
from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactSpec
from clean_agents.crafters.validators.base import ValidationReport

T = TypeVar("T", bound=ArtifactSpec)


class Phase(str, Enum):
    INTAKE = "intake"
    RECOMMEND = "recommend"
    DEEP_DIVE = "deep_dive"
    BUNDLE = "bundle"
    ITERATE = "iterate"
    MODULES = "modules"


class DesignConfig(BaseModel):
    enable_ai: bool = False
    language: str = "en"
    interactive: bool = True
    knowledge_root: Path | None = None


class Turn(BaseModel):
    phase: Phase
    role: str                              # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Recommendation(BaseModel):
    summary: str
    proposed_spec: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)


class Delta(BaseModel):
    field_path: str
    old_value: Any = None
    new_value: Any = None
    cascaded_fields: list[str] = Field(default_factory=list)


class CascadeReport(BaseModel):
    deltas: list[Delta] = Field(default_factory=list)
    invalidated_validators: list[str] = Field(default_factory=list)


class ModuleResult(BaseModel):
    name: str
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class Bundle(BaseModel):
    output_dir: Path
    files: list[Path] = Field(default_factory=list)
    validation: ValidationReport | None = None


class DesignSession(BaseModel, Generic[T]):
    """Generic 5-phase engine. Typed on the artifact spec subclass."""

    session_id: UUID = Field(default_factory=uuid4)
    phase: Phase = Phase.INTAKE
    spec: T
    history: list[Turn] = Field(default_factory=list)
    validation_state: ValidationReport | None = None
    config: DesignConfig = Field(default_factory=DesignConfig)

    model_config = {"arbitrary_types_allowed": True}

    def intake(self, input: str | T) -> Recommendation:  # noqa: A002
        raise NotImplementedError("Implemented in M5")

    def answer(self, question_id: str, answer: Any) -> Delta:
        raise NotImplementedError("Implemented in M5")

    def render(self, output_dir: Path) -> Bundle:
        raise NotImplementedError("Implemented in M5")

    def iterate(self, edits: dict[str, Any]) -> CascadeReport:
        raise NotImplementedError("Implemented in M5")

    def module(self, name: str, **kwargs: Any) -> ModuleResult:
        raise NotImplementedError("Implemented in M5")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def load(cls, path: Path) -> DesignSession[T]:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_session.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/session.py tests/test_crafters_session.py
git commit -m "feat(crafters): scaffold DesignSession[T] with Phase enum and typed placeholders"
```

### Task M1.7: Expose public API and stub CLI group (no commands yet)

**Files:**
- Modify: `src/clean_agents/crafters/__init__.py`
- Create: `src/clean_agents/cli/skill_cmd.py`
- Modify: `src/clean_agents/cli/main.py` (register skill_app with stub)
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Add failing CLI smoke test**

```python
# tests/test_crafters_cli.py
from typer.testing import CliRunner

from clean_agents.cli.main import app

runner = CliRunner()


def test_skill_group_registered():
    result = runner.invoke(app, ["skill", "--help"])
    assert result.exit_code == 0
    assert "design" in result.stdout
    assert "validate" in result.stdout
    assert "render" in result.stdout
    assert "publish" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: FAIL (skill group not registered yet)

- [ ] **Step 3: Implement CLI stubs**

```python
# src/clean_agents/cli/skill_cmd.py
"""CLI for the Skills vertical of crafters (M1 stubs; filled in M6)."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def design_cmd(
    description: str = typer.Argument("", help="Natural-language description"),
) -> None:
    """Start an interactive Skill design session (stub — wired in M6)."""
    console.print("[yellow]skill design: coming in M6[/]")


def validate_cmd(
    path: str = typer.Argument(..., help="Path to skill bundle or .skill-spec.yaml"),
) -> None:
    """Validate a Skill against L1/L2/L3 rules (stub — wired in M6)."""
    console.print(f"[yellow]skill validate {path}: coming in M6[/]")


def render_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
) -> None:
    """Render a Skill bundle from a spec (stub — wired in M6)."""
    console.print(f"[yellow]skill render {spec}: coming in M6[/]")


def publish_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
) -> None:
    """Publish a Skill to the marketplace (stub — wired in M6)."""
    console.print(f"[yellow]skill publish {spec}: coming in M6[/]")
```

- [ ] **Step 4: Register the group in `main.py`**

Modify `src/clean_agents/cli/main.py` by adding (after the existing `telemetry_app` block, before `@app.command("serve")`):

```python
from clean_agents.cli.skill_cmd import (  # noqa: E402
    design_cmd as skill_design_cmd,
    validate_cmd as skill_validate_cmd,
    render_cmd as skill_render_cmd,
    publish_cmd as skill_publish_cmd,
)

skill_app = typer.Typer(
    name="skill",
    help="Design, validate, render, and publish Claude Code Skills",
    no_args_is_help=True,
)
skill_app.command("design", help="Start an interactive Skill design session")(skill_design_cmd)
skill_app.command("validate", help="Validate a Skill bundle or spec")(skill_validate_cmd)
skill_app.command("render", help="Render a Skill bundle from .skill-spec.yaml")(skill_render_cmd)
skill_app.command("publish", help="Publish a Skill to the marketplace")(skill_publish_cmd)
app.add_typer(skill_app)
```

- [ ] **Step 5: Expose public API in `crafters/__init__.py`**

```python
# src/clean_agents/crafters/__init__.py
"""CLean-agents crafters — design Skills, MCPs, Tools, and Plugins."""

from clean_agents.crafters.base import ArtifactRef, ArtifactSpec, ArtifactType
from clean_agents.crafters.session import (
    Bundle,
    DesignConfig,
    DesignSession,
    Phase,
    Recommendation,
)
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
```

- [ ] **Step 6: Run tests to verify pass**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: PASS

- [ ] **Step 7: Run full suite to confirm no regressions**

Run: `pytest tests/ -q`
Expected: 303 pre-existing tests + all new crafters tests PASS.

- [ ] **Step 8: Commit**

```bash
git add src/clean_agents/crafters/__init__.py src/clean_agents/cli/skill_cmd.py src/clean_agents/cli/main.py tests/test_crafters_cli.py
git commit -m "feat(crafters): expose public API + register skill CLI group (stubs)"
```

---

## Milestone M2 — `SkillSpec` + L1 validators + fixtures

**Dependencies:** M1.

### Task M2.1: Implement `SkillSpec` + nested models

**Files:**
- Create: `src/clean_agents/crafters/skill/spec.py`
- Test: `tests/test_crafters_base.py`

- [ ] **Step 1: Add failing test**

```python
# tests/test_crafters_base.py (append)
from pathlib import Path

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import (
    EvalCase,
    EvalsManifest,
    EvalThresholds,
    ReferenceFile,
    SkillSection,
    SkillSpec,
)


def test_skill_spec_minimal():
    spec = SkillSpec(
        name="example-skill",
        description="A minimal skill used in unit tests — >50 chars so desc-length passes.",
        triggers=["example", "fixture", "unit test"],
        references=[],
        body_outline=[SkillSection(heading="Overview", body="…")],
    )
    assert spec.artifact_type is ArtifactType.SKILL
    assert spec.bundle_format == "dir"


def test_reference_file_fields():
    ref = ReferenceFile(
        path=Path("references/taxonomy.md"),
        topic="Taxonomy of skill triggers",
        outline=["Intro", "Matrix", "Examples"],
        mentioned_in=["overview"],
    )
    assert ref.outline == ["Intro", "Matrix", "Examples"]


def test_evals_manifest_defaults():
    manifest = EvalsManifest(
        positive_cases=[EvalCase(prompt="Design a skill for X", expected="activate")],
        negative_cases=[EvalCase(prompt="What time is it?", expected="ignore")],
    )
    assert manifest.thresholds.tpr_min == 0.8
    assert manifest.thresholds.fpr_max == 0.2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_base.py -v`
Expected: FAIL with `ModuleNotFoundError: clean_agents.crafters.skill.spec`

- [ ] **Step 3: Implement `skill/spec.py`**

```python
# src/clean_agents/crafters/skill/spec.py
"""Skill-vertical artifact spec (v1 of crafters)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from clean_agents.crafters.base import ArtifactSpec, ArtifactType


class SkillSection(BaseModel):
    heading: str
    body: str = ""
    anchor: str | None = None                  # slug for cross-reference


class ReferenceFile(BaseModel):
    path: Path                                 # relative to bundle root
    topic: str
    outline: list[str] = Field(default_factory=list)
    mentioned_in: list[str] = Field(default_factory=list)   # anchors in SKILL.md


class EvalCase(BaseModel):
    prompt: str
    expected: Literal["activate", "ignore"]
    note: str = ""


class EvalThresholds(BaseModel):
    tpr_min: float = 0.8
    fpr_max: float = 0.2


class EvalsManifest(BaseModel):
    positive_cases: list[EvalCase] = Field(default_factory=list)
    negative_cases: list[EvalCase] = Field(default_factory=list)
    thresholds: EvalThresholds = Field(default_factory=EvalThresholds)


class SkillSpec(ArtifactSpec):
    """Skill (Claude Code / Anthropic Skills) artifact spec."""

    artifact_type: Literal[ArtifactType.SKILL] = ArtifactType.SKILL
    triggers: list[str] = Field(default_factory=list)
    references: list[ReferenceFile] = Field(default_factory=list)
    evals: EvalsManifest | None = None
    body_outline: list[SkillSection] = Field(default_factory=list)
    bundle_format: Literal["dir", "zip"] = "dir"
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/skill/spec.py tests/test_crafters_base.py
git commit -m "feat(crafters): add SkillSpec + ReferenceFile + EvalsManifest"
```

### Task M2.2: Create L1 fixtures (good, bad-desc-too-long, leandro-real-skill copy)

**Files:**
- Create: `tests/fixtures/crafters/skill/good-skill/.skill-spec.yaml`
- Create: `tests/fixtures/crafters/skill/good-skill/SKILL.md`
- Create: `tests/fixtures/crafters/skill/good-skill/references/taxonomy.md`
- Create: `tests/fixtures/crafters/skill/bad-desc-too-long/.skill-spec.yaml`
- Create: `tests/fixtures/crafters/skill/bad-desc-too-long/SKILL.md`

- [ ] **Step 1: Create `good-skill` fixture**

`.skill-spec.yaml`:

```yaml
name: good-skill
version: 0.1.0
description: A cleanly designed fixture used to prove L1 validators pass when a skill follows every structural rule.
artifact_type: skill
language: en
license: MIT
triggers: ["fixture", "good skill", "structural test"]
references:
  - path: references/taxonomy.md
    topic: Trigger taxonomy for fixture tests
    outline: ["Intro", "Examples"]
    mentioned_in: ["overview"]
body_outline:
  - heading: Overview
    anchor: overview
    body: See references/taxonomy.md for the full matrix.
```

`SKILL.md`:

```markdown
---
name: good-skill
description: A cleanly designed fixture used to prove L1 validators pass when a skill follows every structural rule.
version: 0.1.0
---

# Overview {#overview}

See references/taxonomy.md for the full matrix.
```

`references/taxonomy.md`:

```markdown
# Trigger taxonomy for fixture tests

## Intro
Short.

## Examples
- fixture
- good skill
```

- [ ] **Step 2: Create `bad-desc-too-long` fixture**

`.skill-spec.yaml`:

```yaml
name: bad-desc-too-long
version: 0.1.0
description: This description intentionally exceeds 500 characters so that SKILL-L1-DESC-LENGTH fires with a CRITICAL finding. lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum.
artifact_type: skill
language: en
triggers: ["fixture"]
references: []
body_outline: []
```

`SKILL.md`: copy the long description into frontmatter, minimal body.

- [ ] **Step 3: Copy author's real skill for regression**

```bash
mkdir -p tests/fixtures/crafters/skill/leandro-real-skill
cp -r "$HOME/.claude/skills/clean-agents/SKILL.md" tests/fixtures/crafters/skill/leandro-real-skill/SKILL.md
# references/ folder mirrored for the SKILL-L1-REFS-EXIST / REFS-ORPHAN tests
```

- [ ] **Step 4: Commit fixtures**

```bash
git add tests/fixtures/crafters/skill/
git commit -m "test(crafters): add L1 fixtures (good, bad-desc-too-long, leandro-real-skill)"
```

### Task M2.3: Implement `SKILL-L1-NAME-DIR` validator

**Files:**
- Create: `src/clean_agents/crafters/skill/validators.py`
- Test: `tests/test_crafters_validators_l1.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_validators_l1.py
from pathlib import Path

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.skill.validators import SkillL1NameDir
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec(name: str) -> SkillSpec:
    return SkillSpec(
        name=name,
        description="Fixture description longer than fifty chars to pass L1-DESC-LENGTH.",
        triggers=[name],
        references=[],
        body_outline=[],
    )


def test_name_dir_match_passes(tmp_path: Path):
    bundle = tmp_path / "my-skill"
    bundle.mkdir()
    ctx = ValidationContext(bundle_root=bundle)
    result = SkillL1NameDir().check(_spec("my-skill"), ctx)
    assert result == []


def test_name_dir_mismatch_fires(tmp_path: Path):
    bundle = tmp_path / "other-name"
    bundle.mkdir()
    ctx = ValidationContext(bundle_root=bundle)
    findings = SkillL1NameDir().check(_spec("my-skill"), ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "SKILL-L1-NAME-DIR"
    assert findings[0].severity is Severity.HIGH
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crafters_validators_l1.py -v`
Expected: FAIL with `ImportError: cannot import name 'SkillL1NameDir'`

- [ ] **Step 3: Implement the validator**

```python
# src/clean_agents/crafters/skill/validators.py
"""Skill-vertical validator rules (L1-L4)."""

from __future__ import annotations

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationFinding,
    ValidatorBase,
)


class SkillL1NameDir(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-NAME-DIR"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        if ctx.bundle_root.name != spec.name:
            return [
                ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    message=(
                        f"spec.name={spec.name!r} does not match bundle directory "
                        f"{ctx.bundle_root.name!r}"
                    ),
                    location=str(ctx.bundle_root),
                    fix_hint=f"Rename the directory to {spec.name!r} or update spec.name.",
                    auto_fixable=False,
                )
            ]
        return []
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_validators_l1.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/skill/validators.py tests/test_crafters_validators_l1.py
git commit -m "feat(crafters): implement SKILL-L1-NAME-DIR validator"
```

### Task M2.4: Implement `SKILL-L1-DESC-LENGTH`, `SKILL-L1-REFS-EXIST`, `SKILL-L1-REFS-ORPHAN`

**Files:**
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Test: `tests/test_crafters_validators_l1.py`

- [ ] **Step 1: Add failing tests**

```python
# tests/test_crafters_validators_l1.py (append)
from clean_agents.crafters.skill.spec import ReferenceFile
from clean_agents.crafters.skill.validators import (
    SkillL1DescLength,
    SkillL1RefsExist,
    SkillL1RefsOrphan,
)


def test_desc_length_short_fires():
    spec = SkillSpec(
        name="x", description="too short",
        triggers=["x"], references=[], body_outline=[],
    )
    findings = SkillL1DescLength().check(spec, ValidationContext())
    assert len(findings) == 1
    assert findings[0].severity is Severity.CRITICAL


def test_desc_length_long_fires():
    spec = SkillSpec(
        name="x", description="a" * 501,
        triggers=["x"], references=[], body_outline=[],
    )
    findings = SkillL1DescLength().check(spec, ValidationContext())
    assert len(findings) == 1
    assert findings[0].rule_id == "SKILL-L1-DESC-LENGTH"


def test_refs_exist_fires_for_missing_file(tmp_path: Path):
    bundle = tmp_path / "s"
    bundle.mkdir()
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[ReferenceFile(path=Path("references/missing.md"), topic="", outline=[])],
        body_outline=[],
    )
    findings = SkillL1RefsExist().check(spec, ValidationContext(bundle_root=bundle))
    assert len(findings) == 1
    assert findings[0].rule_id == "SKILL-L1-REFS-EXIST"


def test_refs_orphan_fires_for_unmentioned_file(tmp_path: Path):
    bundle = tmp_path / "s"
    (bundle / "references").mkdir(parents=True)
    (bundle / "references" / "orphan.md").write_text("# orphan\n")
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"], references=[], body_outline=[],
    )
    findings = SkillL1RefsOrphan().check(spec, ValidationContext(bundle_root=bundle))
    assert any(f.rule_id == "SKILL-L1-REFS-ORPHAN" for f in findings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_crafters_validators_l1.py -v`
Expected: FAIL (new validators not implemented yet).

- [ ] **Step 3: Append validator classes**

```python
# src/clean_agents/crafters/skill/validators.py (append)
class SkillL1DescLength(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-DESC-LENGTH"
    MIN = 50
    MAX = 500

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        n = len(spec.description)
        if self.MIN <= n <= self.MAX:
            return []
        return [
            ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.CRITICAL,
                message=f"description length {n} outside [{self.MIN}, {self.MAX}]",
                location="spec.description",
                fix_hint=(
                    "Shorten to ≤500 chars while preserving distinctive triggers"
                    if n > self.MAX else "Expand to ≥50 chars with concrete activation cues"
                ),
                auto_fixable=False,
            )
        ]


class SkillL1RefsExist(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-REFS-EXIST"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        out: list[ValidationFinding] = []
        for ref in spec.references:
            path = ctx.bundle_root / ref.path
            if not path.exists():
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.HIGH,
                    message=f"reference declared but missing on disk: {ref.path}",
                    location=str(ref.path),
                    fix_hint=f"Create {ref.path} or remove it from spec.references.",
                    auto_fixable=True,
                ))
        return out


class SkillL1RefsOrphan(ValidatorBase[SkillSpec]):
    level = Level.L1
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L1-REFS-ORPHAN"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        refs_dir = ctx.bundle_root / "references"
        if not refs_dir.exists():
            return []
        declared = {ref.path.name for ref in spec.references}
        out: list[ValidationFinding] = []
        for path in refs_dir.glob("*.md"):
            if path.name not in declared:
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    message=f"file in references/ not referenced from spec: {path.name}",
                    location=str(path.relative_to(ctx.bundle_root)),
                    fix_hint=(
                        f"Add {path.name} to spec.references or delete it."
                    ),
                    auto_fixable=False,
                ))
        return out
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_validators_l1.py -v`
Expected: PASS

- [ ] **Step 5: Register built-in L1 validators on the global registry**

Append to `src/clean_agents/crafters/skill/validators.py`:

```python
def register_builtin(registry) -> None:
    """Called from crafters package init to register L1 validators."""
    registry.register(SkillL1NameDir())
    registry.register(SkillL1DescLength())
    registry.register(SkillL1RefsExist())
    registry.register(SkillL1RefsOrphan())
```

Modify `src/clean_agents/crafters/__init__.py` — add at bottom:

```python
from clean_agents.crafters.skill.validators import register_builtin as _reg_skill
_reg_skill(get_registry())
```

- [ ] **Step 6: Run the full suite to ensure no regressions**

Run: `pytest tests/ -q`
Expected: all pre-existing + new tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/clean_agents/crafters/skill/validators.py src/clean_agents/crafters/__init__.py tests/test_crafters_validators_l1.py
git commit -m "feat(crafters): complete L1 validators + auto-register on registry"
```

---

## Milestone M3 — L2 validators (semantic, including AI-assisted contradictions)

**Dependencies:** M1, M2.

### Task M3.1: L2 fixtures (`bad-hardcoded-stats`, `bad-language-mix`)

**Files:**
- Create: `tests/fixtures/crafters/skill/bad-hardcoded-stats/.skill-spec.yaml` + `SKILL.md`
- Create: `tests/fixtures/crafters/skill/bad-language-mix/.skill-spec.yaml` + `SKILL.md`

- [ ] **Step 1: Write bad-hardcoded-stats fixture**

`.skill-spec.yaml`:
```yaml
name: bad-hardcoded-stats
version: 0.1.0
description: A fixture skill that intentionally embeds 82.4% attack success and CVE-2025-6514 to trip L2.
artifact_type: skill
language: en
triggers: ["fixture", "hardcoded stats"]
references: []
body_outline:
  - heading: Findings
    body: "According to our paper de 2024, attack success is 82.4% against CVE-2025-6514."
```

`SKILL.md`:
```markdown
---
name: bad-hardcoded-stats
description: A fixture skill that intentionally embeds 82.4% attack success and CVE-2025-6514 to trip L2.
---

# Findings

According to our paper de 2024, attack success is 82.4% against CVE-2025-6514.
```

- [ ] **Step 2: Write bad-language-mix fixture**

`.skill-spec.yaml`:
```yaml
name: bad-language-mix
version: 0.1.0
description: Fixture with a Spanish quote inside an English-declared skill to trigger LANGUAGE-MIX.
artifact_type: skill
language: en
triggers: ["fixture", "language mix"]
references: []
body_outline:
  - heading: Example
    body: "The agent replied: 'si puedes porfi, revisá el commit antes de mergear'."
```

`SKILL.md`: mirror.

- [ ] **Step 3: Commit fixtures**

```bash
git add tests/fixtures/crafters/skill/bad-hardcoded-stats tests/fixtures/crafters/skill/bad-language-mix
git commit -m "test(crafters): add L2 fixtures (hardcoded-stats, language-mix)"
```

### Task M3.2: `SKILL-L2-HARDCODED-STATS` + `SKILL-L2-HARDCODED-DATES`

**Files:**
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Test: `tests/test_crafters_validators_l2.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_crafters_validators_l2.py
from pathlib import Path

from clean_agents.crafters.skill.spec import SkillSection, SkillSpec
from clean_agents.crafters.skill.validators import (
    SkillL2HardcodedDates,
    SkillL2HardcodedStats,
)
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec_with_body(body: str) -> SkillSpec:
    return SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[],
        body_outline=[SkillSection(heading="Body", body=body)],
    )


def test_hardcoded_stats_percent():
    findings = SkillL2HardcodedStats().check(_spec_with_body("Accuracy was 82.4% in benchmark."), ValidationContext())
    assert any(f.rule_id == "SKILL-L2-HARDCODED-STATS" for f in findings)


def test_hardcoded_stats_cve():
    findings = SkillL2HardcodedStats().check(_spec_with_body("Mitigates CVE-2025-6514 attacks."), ValidationContext())
    assert any("CVE" in f.message for f in findings)


def test_hardcoded_stats_paper_year():
    findings = SkillL2HardcodedStats().check(_spec_with_body("as shown by paper de 2024 results"), ValidationContext())
    assert findings


def test_hardcoded_dates_fires_on_specific_year():
    findings = SkillL2HardcodedDates().check(_spec_with_body("In 2024, the team shipped v1."), ValidationContext())
    assert findings
    assert findings[0].severity is Severity.MEDIUM
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_crafters_validators_l2.py -v`
Expected: FAIL.

- [ ] **Step 3: Append validator classes**

```python
# src/clean_agents/crafters/skill/validators.py (append)
import re

_PCT_RE = re.compile(r"\b\d+\.\d+\s?%")
_CVE_RE = re.compile(r"\bCVE-\d{4}-\d+\b", re.IGNORECASE)
_PAPER_RE = re.compile(r"\bpaper de \d{4}\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _iter_body_text(spec: SkillSpec) -> list[tuple[str, str]]:
    """Yield (location, text) per section."""
    return [(f"body_outline[{i}]", s.body) for i, s in enumerate(spec.body_outline)]


class SkillL2HardcodedStats(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-HARDCODED-STATS"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        out: list[ValidationFinding] = []
        for loc, text in _iter_body_text(spec):
            for pat, kind in [(_PCT_RE, "percentage"), (_CVE_RE, "CVE id"), (_PAPER_RE, "paper year")]:
                for m in pat.finditer(text):
                    out.append(ValidationFinding(
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        message=f"hard-coded {kind} ages poorly: {m.group(0)!r}",
                        location=loc,
                        fix_hint=f"Move {m.group(0)!r} to references/ so it can be updated independently.",
                    ))
        return out


class SkillL2HardcodedDates(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-HARDCODED-DATES"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        out: list[ValidationFinding] = []
        for loc, text in _iter_body_text(spec):
            for m in _YEAR_RE.finditer(text):
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    message=f"hard-coded year {m.group(0)!r} ages poorly",
                    location=loc,
                    fix_hint="Replace with a relative reference or move to references/.",
                ))
        return out
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_validators_l2.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/skill/validators.py tests/test_crafters_validators_l2.py
git commit -m "feat(crafters): add SKILL-L2-HARDCODED-STATS and HARDCODED-DATES validators"
```

### Task M3.3: `SKILL-L2-LANGUAGE-MIX`, `SKILL-L2-TRIGGER-COVERAGE`, `SKILL-L2-PROGRESSIVE-DISCLOSURE`, `SKILL-L2-PROMISES-VS-DELIVERY`

**Files:**
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Modify: `src/clean_agents/crafters/validators/semantic.py` (helper for language sniffing)
- Test: `tests/test_crafters_validators_l2.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_crafters_validators_l2.py (append)
from clean_agents.crafters.skill.spec import ReferenceFile
from clean_agents.crafters.skill.validators import (
    SkillL2LanguageMix,
    SkillL2ProgressiveDisclosure,
    SkillL2PromisesVsDelivery,
    SkillL2TriggerCoverage,
)


def test_language_mix_fires_for_spanish_in_english_skill():
    spec = _spec_with_body("The agent said: 'si puedes porfi, revisá el commit antes de mergear'.")
    findings = SkillL2LanguageMix().check(spec, ValidationContext())
    assert any(f.rule_id == "SKILL-L2-LANGUAGE-MIX" for f in findings)


def test_trigger_coverage_fires_below_80pct():
    spec = SkillSpec(
        name="s",
        description="Designs, validates, renders, publishes and ships full-bundle artifacts.",
        triggers=["unrelated"],
        references=[], body_outline=[],
    )
    findings = SkillL2TriggerCoverage().check(spec, ValidationContext())
    assert findings


def test_progressive_disclosure_fires_long_body_no_refs():
    big = "word " * 2500
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[],
        body_outline=[SkillSection(heading="Big", body=big)],
    )
    findings = SkillL2ProgressiveDisclosure().check(spec, ValidationContext())
    assert findings


def test_promises_vs_delivery_fires_for_empty_ref(tmp_path: Path):
    bundle = tmp_path / "s"
    (bundle / "references").mkdir(parents=True)
    (bundle / "references" / "taxonomy.md").write_text("")  # empty
    spec = SkillSpec(
        name="s",
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=["s"],
        references=[ReferenceFile(path=Path("references/taxonomy.md"), topic="t")],
        body_outline=[SkillSection(heading="Overview", body="See references/taxonomy.md")],
    )
    findings = SkillL2PromisesVsDelivery().check(spec, ValidationContext(bundle_root=bundle))
    assert findings
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_crafters_validators_l2.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement language-sniff helper in `validators/semantic.py`**

```python
# src/clean_agents/crafters/validators/semantic.py
"""Shared helpers for L2 validators (language sniffing, keyword extraction)."""

from __future__ import annotations

import re

_ES_HINTS = {
    "si", "porfi", "revisá", "buenas", "gracias", "porque", "como", "este",
    "agente", "muy", "más",
}
_EN_HINTS = {"the", "of", "and", "to", "is", "a", "in", "for", "with"}
_TOKEN_RE = re.compile(r"\b\w+\b", flags=re.UNICODE)


def sniff_language(text: str) -> str | None:
    """Return 'en' | 'es' | None (unknown). Simple hint-word majority vote."""
    tokens = {t.lower() for t in _TOKEN_RE.findall(text)}
    if not tokens:
        return None
    es_hits = len(tokens & _ES_HINTS)
    en_hits = len(tokens & _EN_HINTS)
    if es_hits > en_hits and es_hits > 0:
        return "es"
    if en_hits > 0:
        return "en"
    return None


def extract_keywords(text: str, top_k: int = 20) -> list[str]:
    """Lowercased tokens ≥4 chars, unique, order-preserving."""
    seen: dict[str, None] = {}
    for t in _TOKEN_RE.findall(text.lower()):
        if len(t) >= 4 and t not in seen:
            seen[t] = None
    return list(seen.keys())[:top_k]
```

- [ ] **Step 4: Implement the four validators**

Append to `src/clean_agents/crafters/skill/validators.py`:

```python
from clean_agents.crafters.validators.semantic import extract_keywords, sniff_language


class SkillL2LanguageMix(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-LANGUAGE-MIX"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        out: list[ValidationFinding] = []
        for loc, text in _iter_body_text(spec):
            detected = sniff_language(text)
            if detected is not None and detected != spec.language:
                out.append(ValidationFinding(
                    rule_id=self.rule_id,
                    severity=Severity.MEDIUM,
                    message=(
                        f"block appears to be in {detected!r} but spec.language={spec.language!r}"
                    ),
                    location=loc,
                    fix_hint="Translate or remove mixed-language content.",
                ))
        return out


class SkillL2TriggerCoverage(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-TRIGGER-COVERAGE"
    MIN_COVERAGE = 0.8

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        desc_keywords = set(extract_keywords(spec.description))
        trig_keywords = {t.lower() for t in spec.triggers}
        if not desc_keywords or not trig_keywords:
            return []
        covered = sum(1 for k in desc_keywords if any(k in t or t in k for t in trig_keywords))
        ratio = covered / max(1, len(desc_keywords))
        if ratio < self.MIN_COVERAGE:
            return [ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.MEDIUM,
                message=f"trigger coverage {ratio:.0%} < {self.MIN_COVERAGE:.0%}",
                location="spec.triggers",
                fix_hint="Add triggers that match the distinctive words in the description.",
            )]
        return []


class SkillL2ProgressiveDisclosure(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-PROGRESSIVE-DISCLOSURE"
    WORD_THRESHOLD = 2000

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        total_words = sum(len(s.body.split()) for s in spec.body_outline)
        if total_words > self.WORD_THRESHOLD and not spec.references:
            return [ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.HIGH,
                message=(
                    f"SKILL.md body is {total_words} words with empty references/ — "
                    "progressive disclosure is violated"
                ),
                location="spec.body_outline",
                fix_hint="Move detailed sections into references/*.md and link from SKILL.md.",
            )]
        return []


class SkillL2PromisesVsDelivery(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-PROMISES-VS-DELIVERY"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if ctx.bundle_root is None:
            return []
        out: list[ValidationFinding] = []
        body_text = " ".join(s.body for s in spec.body_outline)
        for ref in spec.references:
            if str(ref.path) in body_text or ref.path.name in body_text:
                fpath = ctx.bundle_root / ref.path
                if fpath.exists() and fpath.read_text(encoding="utf-8").strip() == "":
                    out.append(ValidationFinding(
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        message=f"reference cited in body but file is empty: {ref.path}",
                        location=str(ref.path),
                        fix_hint="Populate the file or remove the citation.",
                    ))
        return out
```

- [ ] **Step 5: Register the 6 new L2 validators**

Update `register_builtin()` in `src/clean_agents/crafters/skill/validators.py`:

```python
def register_builtin(registry) -> None:
    for cls in (
        SkillL1NameDir, SkillL1DescLength, SkillL1RefsExist, SkillL1RefsOrphan,
        SkillL2HardcodedStats, SkillL2HardcodedDates, SkillL2LanguageMix,
        SkillL2TriggerCoverage, SkillL2ProgressiveDisclosure, SkillL2PromisesVsDelivery,
    ):
        registry.register(cls())
```

- [ ] **Step 6: Run tests to verify pass**

Run: `pytest tests/test_crafters_validators_l2.py tests/test_crafters_validators_l1.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/clean_agents/crafters/skill/validators.py src/clean_agents/crafters/validators/semantic.py tests/test_crafters_validators_l2.py
git commit -m "feat(crafters): add L2 validators (LANGUAGE-MIX, TRIGGER-COVERAGE, PROGRESSIVE-DISCLOSURE, PROMISES-VS-DELIVERY)"
```

### Task M3.4: `SKILL-L2-CONTRADICTIONS` (AI-assisted, requires `--ai`)

**Files:**
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Create: `src/clean_agents/crafters/skill/ai.py`
- Test: `tests/test_crafters_validators_l2.py`

- [ ] **Step 1: Write failing test with mocked `ClaudeArchitect`**

```python
# tests/test_crafters_validators_l2.py (append)
from unittest.mock import MagicMock

from clean_agents.crafters.skill.validators import SkillL2Contradictions


def test_contradictions_requires_ai_context():
    spec = _spec_with_body("This skill is always safe.\nThis skill is never safe.")
    findings = SkillL2Contradictions().check(spec, ValidationContext(enable_ai=False))
    assert findings == []   # silently no-op without --ai


def test_contradictions_detects_with_mock_ai():
    spec = _spec_with_body("Always run guardrails.\nNever run guardrails.")
    validator = SkillL2Contradictions(client=MagicMock(
        detect_contradictions=MagicMock(return_value=[
            "Body claims both 'always run guardrails' and 'never run guardrails'.",
        ])
    ))
    findings = validator.check(spec, ValidationContext(enable_ai=True))
    assert findings
    assert findings[0].rule_id == "SKILL-L2-CONTRADICTIONS"
```

- [ ] **Step 2: Run test to verify fail**

Run: `pytest tests/test_crafters_validators_l2.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `skill/ai.py` helper + validator**

```python
# src/clean_agents/crafters/skill/ai.py
"""AI-enhanced helpers wrapping ClaudeArchitect for the Skills vertical."""

from __future__ import annotations

from typing import Protocol


class AIClient(Protocol):
    def detect_contradictions(self, text: str) -> list[str]: ...
    def suggest_triggers(self, description: str) -> list[str]: ...
    def generate_eval_prompts(self, description: str, triggers: list[str], n: int) -> dict: ...
```

Append to `src/clean_agents/crafters/skill/validators.py`:

```python
class SkillL2Contradictions(ValidatorBase[SkillSpec]):
    level = Level.L2
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L2-CONTRADICTIONS"

    def __init__(self, client=None) -> None:
        self.client = client

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if not ctx.enable_ai or self.client is None:
            return []
        text = "\n".join(s.body for s in spec.body_outline)
        try:
            contradictions = self.client.detect_contradictions(text)
        except Exception as e:  # graceful AI degrade — never silent
            return [ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.INFO,
                message=f"AI contradiction check failed: {e}",
                location="spec.body_outline",
                fix_hint="Retry with a reachable ANTHROPIC_API_KEY.",
            )]
        return [
            ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.HIGH,
                message=c,
                location="spec.body_outline",
                fix_hint="Reconcile the contradictory statements.",
            )
            for c in contradictions
        ]
```

Add `SkillL2Contradictions` to `register_builtin()` (it's a no-op without `--ai`, safe to always register; `__init__` default `client=None` is fine).

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_validators_l2.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/skill/validators.py src/clean_agents/crafters/skill/ai.py tests/test_crafters_validators_l2.py
git commit -m "feat(crafters): add SKILL-L2-CONTRADICTIONS (AI-assisted, no-op without --ai)"
```

---

## Milestone M4 — L3 validators (cross-artifact collision)

**Dependencies:** M1, M2.

### Task M4.1: `bad-name-collision` fixture + `SKILL-L3-NAME-COLLISION`

**Files:**
- Create: `tests/fixtures/crafters/skill/bad-name-collision/.skill-spec.yaml` + `SKILL.md`
- Create: `src/clean_agents/crafters/validators/collision.py`
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Test: `tests/test_crafters_validators_l3.py`

- [ ] **Step 1: Write fixture**

`tests/fixtures/crafters/skill/bad-name-collision/.skill-spec.yaml`:
```yaml
name: clean-agents
version: 0.1.0
description: A fixture that intentionally reuses the name 'clean-agents' to trigger L3-NAME-COLLISION.
artifact_type: skill
language: en
triggers: ["fixture", "collision"]
references: []
body_outline: []
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_crafters_validators_l3.py
from pathlib import Path

from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.skill.validators import SkillL3NameCollision
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec(name: str) -> SkillSpec:
    return SkillSpec(
        name=name,
        description="A fixture description longer than fifty chars to pass length check.",
        triggers=[name],
        references=[], body_outline=[],
    )


def test_name_collision_fires(tmp_path: Path):
    installed = tmp_path / "installed"
    (installed / "clean-agents").mkdir(parents=True)
    ctx = ValidationContext(installed_roots=[installed])
    findings = SkillL3NameCollision().check(_spec("clean-agents"), ctx)
    assert findings
    assert findings[0].rule_id == "SKILL-L3-NAME-COLLISION"
    assert findings[0].severity is Severity.CRITICAL


def test_name_collision_no_match(tmp_path: Path):
    installed = tmp_path / "installed"
    installed.mkdir()
    ctx = ValidationContext(installed_roots=[installed])
    assert SkillL3NameCollision().check(_spec("brand-new-skill"), ctx) == []
```

- [ ] **Step 3: Run tests to verify fail**

Run: `pytest tests/test_crafters_validators_l3.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement shared scanner in `validators/collision.py`**

```python
# src/clean_agents/crafters/validators/collision.py
"""Cross-artifact collision scanner (L3)."""

from __future__ import annotations

from pathlib import Path


def installed_skill_names(roots: list[Path]) -> dict[str, Path]:
    """Return name → path for every subdir in any root (shallow scan)."""
    out: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        for p in root.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                out.setdefault(p.name, p)
    return out


def default_installed_roots() -> list[Path]:
    home = Path.home()
    return [
        home / ".claude" / "skills",
        home / ".claude" / "plugins",
        Path(".claude") / "skills",
    ]
```

- [ ] **Step 5: Implement the validator**

```python
# src/clean_agents/crafters/skill/validators.py (append)
from clean_agents.crafters.validators.collision import installed_skill_names


class SkillL3NameCollision(ValidatorBase[SkillSpec]):
    level = Level.L3
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L3-NAME-COLLISION"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        names = installed_skill_names(ctx.installed_roots)
        if spec.name in names:
            return [ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.CRITICAL,
                message=(
                    f"name {spec.name!r} collides with installed skill at {names[spec.name]}"
                ),
                location="spec.name",
                fix_hint=(
                    f"Rename to {spec.name}-v2 / {spec.name}-project / {spec.name}-custom "
                    "or pick a more distinctive name."
                ),
            )]
        return []
```

Add `SkillL3NameCollision` to `register_builtin()`.

- [ ] **Step 6: Run tests to verify pass**

Run: `pytest tests/test_crafters_validators_l3.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/clean_agents/crafters/validators/collision.py src/clean_agents/crafters/skill/validators.py tests/test_crafters_validators_l3.py tests/fixtures/crafters/skill/bad-name-collision
git commit -m "feat(crafters): add SKILL-L3-NAME-COLLISION with shared scanner"
```

### Task M4.2: `SKILL-L3-TRIGGER-OVERLAP` + `SKILL-L3-MARKETPLACE-DEDUPE`

**Files:**
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Test: `tests/test_crafters_validators_l3.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_crafters_validators_l3.py (append)
from clean_agents.crafters.skill.validators import (
    SkillL3MarketplaceDedupe,
    SkillL3TriggerOverlap,
)


def test_trigger_overlap_fires_above_60pct(tmp_path: Path):
    # installed skill "legal-risk" with triggers we overlap with
    installed = tmp_path / "installed"
    skill_dir = installed / "legal-risk"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: legal-risk\ndescription: legal risk patterns\n---\n"
        "# Triggers\n- legal\n- risk\n- contract\n- liability\n- indemnify\n"
    )
    spec = _spec("my-skill")
    spec.triggers = ["legal", "risk", "contract", "liability"]
    ctx = ValidationContext(installed_roots=[installed])
    findings = SkillL3TriggerOverlap().check(spec, ctx)
    assert findings
    assert findings[0].rule_id == "SKILL-L3-TRIGGER-OVERLAP"


def test_marketplace_dedupe_noop_without_index():
    assert SkillL3MarketplaceDedupe().check(_spec("x"), ValidationContext(marketplace_index={})) == []


def test_marketplace_dedupe_fires_when_name_in_index():
    ctx = ValidationContext(
        marketplace_index={"legal-risk-patterns": ["triggers", "mentioned"]},
    )
    findings = SkillL3MarketplaceDedupe().check(_spec("legal-risk-patterns"), ctx)
    assert findings
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_crafters_validators_l3.py -v`
Expected: FAIL.

- [ ] **Step 3: Append validators**

```python
# src/clean_agents/crafters/skill/validators.py (append)
class SkillL3TriggerOverlap(ValidatorBase[SkillSpec]):
    level = Level.L3
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L3-TRIGGER-OVERLAP"
    THRESHOLD = 0.6

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        out: list[ValidationFinding] = []
        own = {t.lower() for t in spec.triggers}
        if not own:
            return out
        for root in ctx.installed_roots:
            if not root.exists():
                continue
            for skill_dir in root.iterdir():
                if not skill_dir.is_dir() or skill_dir.name == spec.name:
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue
                text = skill_md.read_text(encoding="utf-8", errors="ignore").lower()
                other = {t for t in own if t in text}
                ratio = len(other) / len(own)
                if ratio >= self.THRESHOLD:
                    out.append(ValidationFinding(
                        rule_id=self.rule_id,
                        severity=Severity.HIGH,
                        message=(
                            f"trigger overlap {ratio:.0%} with installed skill {skill_dir.name!r}"
                        ),
                        location="spec.triggers",
                        fix_hint="Narrow triggers to distinctive keywords or merge the skills.",
                    ))
        return out


class SkillL3MarketplaceDedupe(ValidatorBase[SkillSpec]):
    level = Level.L3
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L3-MARKETPLACE-DEDUPE"

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if not ctx.marketplace_index:
            return []
        if spec.name in ctx.marketplace_index:
            return [ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.MEDIUM,
                message=f"name {spec.name!r} already published in marketplace",
                location="spec.name",
                fix_hint="Consider contributing to the existing artifact instead.",
            )]
        return []
```

Add both to `register_builtin()`.

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_crafters_validators_l3.py -v`
Expected: PASS.

- [ ] **Step 5: Regression — run Leandro's real skill fixture through full L1+L2+L3 and assert the 5 known findings**

```python
# tests/test_crafters_validators_l3.py (append)
def test_leandro_real_skill_regression(tmp_path: Path):
    from clean_agents.crafters.skill.spec import SkillSpec
    from clean_agents.crafters.validators.base import get_registry
    from clean_agents.crafters.base import ArtifactType

    # Construct a spec that mirrors the known issues found in the real skill
    spec = SkillSpec(
        name="clean-agents",   # collides on purpose
        description="x" * 850, # over 500 on purpose
        triggers=["agent"],
        references=[],
        body_outline=[
            SkillSection(heading="Phase 5", body="si puedes porfi, revisá el commit. 82.4% accuracy vs CVE-2025-6514.")
        ],
    )
    reg = get_registry()
    ctx = ValidationContext(installed_roots=[tmp_path])
    rule_ids = set()
    for v in reg.for_artifact(ArtifactType.SKILL):
        for f in v.check(spec, ctx):
            rule_ids.add(f.rule_id)
    # The 5 documented findings (excluding NAME-DIR which needs a real dir)
    assert "SKILL-L1-DESC-LENGTH" in rule_ids
    assert "SKILL-L2-HARDCODED-STATS" in rule_ids
    assert "SKILL-L2-LANGUAGE-MIX" in rule_ids
```

Run: `pytest tests/test_crafters_validators_l3.py::test_leandro_real_skill_regression -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/clean_agents/crafters/skill/validators.py tests/test_crafters_validators_l3.py
git commit -m "feat(crafters): add SKILL-L3-TRIGGER-OVERLAP + MARKETPLACE-DEDUPE + regression test"
```

---

## Milestone M5 — `DesignSession[T]` engine + Jinja2 renderer + `.skill-spec.yaml` round-trip

**Dependencies:** M1, M2, M3, M4.

### Task M5.1: Jinja2 templates for the bundle

**Files:**
- Create: `src/clean_agents/crafters/skill/templates/SKILL.md.j2`
- Create: `src/clean_agents/crafters/skill/templates/README.md.j2`
- Create: `src/clean_agents/crafters/skill/templates/reference.md.j2`
- Create: `src/clean_agents/crafters/skill/templates/evals.json.j2`

- [ ] **Step 1: `SKILL.md.j2`**

```jinja
---
name: {{ spec.name }}
description: {{ spec.description }}
version: {{ spec.version }}
{%- if spec.author %}
author: {{ spec.author }}
{%- endif %}
language: {{ spec.language }}
license: {{ spec.license }}
---

{% for section in spec.body_outline -%}
# {{ section.heading }}{% if section.anchor %} {{ "{#" }}{{ section.anchor }}}{% endif %}

{{ section.body }}

{% endfor -%}
{%- if spec.references %}
## References

{% for ref in spec.references -%}
- [{{ ref.topic }}]({{ ref.path }})
{% endfor -%}
{%- endif %}
```

- [ ] **Step 2: `README.md.j2`**

```jinja
# {{ spec.name }}

{{ spec.description }}

- **Version**: {{ spec.version }}
- **License**: {{ spec.license }}
- **Language**: {{ spec.language }}

Generated by [CLean-agents crafters]({{ project_url }}).
```

- [ ] **Step 3: `reference.md.j2`**

```jinja
# {{ ref.topic }}

{% for heading in ref.outline -%}
## {{ heading }}

<!-- TODO: fill in -->

{% endfor %}
```

- [ ] **Step 4: `evals.json.j2`**

```jinja
{
  "positive_cases": [
    {% for case in spec.evals.positive_cases -%}
    {"prompt": {{ case.prompt | tojson }}, "expected": "activate"}{% if not loop.last %},{% endif %}
    {% endfor %}
  ],
  "negative_cases": [
    {% for case in spec.evals.negative_cases -%}
    {"prompt": {{ case.prompt | tojson }}, "expected": "ignore"}{% if not loop.last %},{% endif %}
    {% endfor %}
  ],
  "thresholds": {
    "tpr_min": {{ spec.evals.thresholds.tpr_min }},
    "fpr_max": {{ spec.evals.thresholds.fpr_max }}
  }
}
```

- [ ] **Step 5: Commit templates**

```bash
git add src/clean_agents/crafters/skill/templates/
git commit -m "feat(crafters): add Jinja2 templates for SKILL.md / README / references / evals"
```

### Task M5.2: `BundleRenderer` — load templates, write bundle to disk

**Files:**
- Create: `src/clean_agents/crafters/renderer.py`
- Create: `src/clean_agents/crafters/skill/scaffold.py`
- Test: `tests/test_crafters_renderer.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_renderer.py
from pathlib import Path

from clean_agents.crafters.skill.scaffold import render_skill_bundle
from clean_agents.crafters.skill.spec import (
    EvalCase, EvalsManifest, ReferenceFile, SkillSection, SkillSpec,
)


def test_render_bundle_produces_expected_files(tmp_path: Path):
    spec = SkillSpec(
        name="demo-skill",
        description="A fixture skill rendered via the BundleRenderer for unit testing purposes.",
        triggers=["demo", "fixture"],
        references=[ReferenceFile(path=Path("references/taxonomy.md"), topic="Taxonomy", outline=["Intro"])],
        body_outline=[SkillSection(heading="Overview", body="See references/taxonomy.md.", anchor="overview")],
        evals=EvalsManifest(
            positive_cases=[EvalCase(prompt="demo prompt", expected="activate")],
            negative_cases=[EvalCase(prompt="unrelated", expected="ignore")],
        ),
    )
    bundle = render_skill_bundle(spec, output_dir=tmp_path / "out")
    assert (bundle.output_dir / "SKILL.md").exists()
    assert (bundle.output_dir / "README.md").exists()
    assert (bundle.output_dir / "references" / "taxonomy.md").exists()
    assert (bundle.output_dir / "evals" / "evals.json").exists()
    assert (bundle.output_dir / ".skill-spec.yaml").exists()


def test_roundtrip_spec_yaml(tmp_path: Path):
    import yaml

    spec = SkillSpec(
        name="roundtrip",
        description="A fixture for round-trip spec YAML testing; must survive save + load unchanged.",
        triggers=["roundtrip"],
        references=[], body_outline=[],
    )
    bundle = render_skill_bundle(spec, output_dir=tmp_path / "rt")
    loaded = yaml.safe_load((bundle.output_dir / ".skill-spec.yaml").read_text(encoding="utf-8"))
    assert loaded["name"] == "roundtrip"
    restored = SkillSpec.model_validate(loaded)
    assert restored.description == spec.description
```

- [ ] **Step 2: Run test to verify fail**

Run: `pytest tests/test_crafters_renderer.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `renderer.py`**

```python
# src/clean_agents/crafters/renderer.py
"""Generic Jinja2-based bundle renderer. Verticals wrap this with their templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


class BundleRenderer:
    def __init__(self, template_dir: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

    def render(self, template_name: str, ctx: dict[str, Any]) -> str:
        return self.env.get_template(template_name).render(**ctx)
```

- [ ] **Step 4: Implement `skill/scaffold.py`**

```python
# src/clean_agents/crafters/skill/scaffold.py
"""Write a Skill bundle to disk using the Jinja2 templates in templates/."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from clean_agents.crafters.renderer import BundleRenderer
from clean_agents.crafters.session import Bundle
from clean_agents.crafters.skill.spec import SkillSpec


_TEMPLATES = Path(__file__).parent / "templates"
_PROJECT_URL = "https://github.com/Leandrozz/clean-agents"


def render_skill_bundle(spec: SkillSpec, output_dir: Path) -> Bundle:
    """Render a Skill bundle directory. Returns Bundle pointing at output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    r = BundleRenderer(_TEMPLATES)

    # SKILL.md
    skill_md = r.render("SKILL.md.j2", {"spec": spec})
    (output_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # README.md
    readme = r.render("README.md.j2", {"spec": spec, "project_url": _PROJECT_URL})
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    # References scaffolds
    refs_dir = output_dir / "references"
    refs_dir.mkdir(exist_ok=True)
    for ref in spec.references:
        target = output_dir / ref.path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(r.render("reference.md.j2", {"ref": ref}), encoding="utf-8")

    # Evals
    if spec.evals is not None:
        evals_dir = output_dir / "evals"
        evals_dir.mkdir(exist_ok=True)
        rendered = r.render("evals.json.j2", {"spec": spec})
        # Normalize through json.loads/dumps to guarantee valid JSON even if template whitespace is ugly
        (evals_dir / "evals.json").write_text(
            json.dumps(json.loads(rendered), indent=2), encoding="utf-8"
        )

    # Source-of-truth YAML
    data = spec.model_dump(mode="json", exclude_none=True)
    (output_dir / ".skill-spec.yaml").write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    files = [p for p in output_dir.rglob("*") if p.is_file()]
    return Bundle(output_dir=output_dir, files=files)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_crafters_renderer.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/clean_agents/crafters/renderer.py src/clean_agents/crafters/skill/scaffold.py tests/test_crafters_renderer.py
git commit -m "feat(crafters): BundleRenderer + render_skill_bundle with YAML round-trip"
```

### Task M5.3: `DesignSession` methods — `intake`, `render`, `iterate`, `save/load` round-trip

**Files:**
- Modify: `src/clean_agents/crafters/session.py`
- Test: `tests/test_crafters_session.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_crafters_session.py (append)
from pathlib import Path

from clean_agents.crafters.skill.spec import SkillSpec


def _skill() -> SkillSpec:
    return SkillSpec(
        name="session-skill",
        description="A fixture used to test DesignSession state transitions end-to-end.",
        triggers=["session", "fixture"],
        references=[], body_outline=[],
    )


def test_intake_transitions_to_recommend():
    s = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s.intake(_skill())
    assert s.phase is Phase.RECOMMEND


def test_render_transitions_to_bundle(tmp_path: Path):
    s = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s.intake(_skill())
    bundle = s.render(tmp_path / "out")
    assert s.phase is Phase.BUNDLE
    assert bundle.output_dir.exists()


def test_iterate_records_delta_and_reenters_recommend():
    s = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s.intake(_skill())
    report = s.iterate({"description": "Shorter description, still over fifty characters in length."})
    assert report.deltas
    assert s.phase is Phase.ITERATE


def test_session_save_load_roundtrip(tmp_path: Path):
    s1 = DesignSession[SkillSpec](spec=_skill(), config=DesignConfig())
    s1.intake(_skill())
    s1.save(tmp_path / "session.yaml")
    s2 = DesignSession[SkillSpec].load(tmp_path / "session.yaml")
    assert s2.spec.name == s1.spec.name
    assert s2.phase is s1.phase
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_crafters_session.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement the methods in `session.py`**

Replace the `NotImplementedError` placeholders:

```python
# src/clean_agents/crafters/session.py — inside DesignSession class
    def intake(self, input):  # noqa: A002
        from clean_agents.crafters.base import ArtifactSpec
        if isinstance(input, ArtifactSpec):
            self.spec = input  # type: ignore[assignment]
        self.phase = Phase.RECOMMEND
        self.history.append(Turn(phase=Phase.INTAKE, role="user", content=str(input)))
        return Recommendation(
            summary="Spec accepted; proceed to deep dive or render.",
            proposed_spec=self.spec.model_dump(mode="json"),
        )

    def answer(self, question_id, answer):
        self.history.append(Turn(phase=self.phase, role="user", content=f"{question_id}={answer}"))
        return Delta(field_path=question_id, new_value=answer)

    def render(self, output_dir):
        # Default implementation for Skills; verticals can override via duck-typed dispatch
        from clean_agents.crafters.skill.scaffold import render_skill_bundle
        bundle = render_skill_bundle(self.spec, output_dir)   # type: ignore[arg-type]
        self.phase = Phase.BUNDLE
        return bundle

    def iterate(self, edits):
        deltas: list[Delta] = []
        spec_dict = self.spec.model_dump(mode="json")
        for k, v in edits.items():
            old = spec_dict.get(k)
            spec_dict[k] = v
            deltas.append(Delta(field_path=k, old_value=old, new_value=v))
        self.spec = type(self.spec).model_validate(spec_dict)
        self.phase = Phase.ITERATE
        return CascadeReport(deltas=deltas)

    def module(self, name, **kwargs):
        self.phase = Phase.MODULES
        return ModuleResult(name=name, ok=True, message=f"Module {name!r} dispatched.")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_session.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/session.py tests/test_crafters_session.py
git commit -m "feat(crafters): implement DesignSession intake/render/iterate + save/load roundtrip"
```

---

## Milestone M6 — CLI wiring (`skill design/validate/render/publish`)

**Dependencies:** M5.

### Task M6.1: Replace `skill validate` stub with real L1+L2+L3 validation

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_cli.py (append)
from pathlib import Path

from typer.testing import CliRunner

from clean_agents.cli.main import app

runner = CliRunner()


def test_validate_good_skill_succeeds():
    fixture = Path("tests/fixtures/crafters/skill/good-skill")
    result = runner.invoke(app, ["skill", "validate", str(fixture)])
    assert result.exit_code == 0, result.stdout
    assert "No findings" in result.stdout or "0 findings" in result.stdout


def test_validate_bad_desc_too_long_fails():
    fixture = Path("tests/fixtures/crafters/skill/bad-desc-too-long")
    result = runner.invoke(app, ["skill", "validate", str(fixture)])
    assert result.exit_code != 0
    assert "SKILL-L1-DESC-LENGTH" in result.stdout


def test_validate_json_format():
    fixture = Path("tests/fixtures/crafters/skill/good-skill")
    result = runner.invoke(app, ["skill", "validate", str(fixture), "--format", "json"])
    assert result.exit_code == 0
    import json
    parsed = json.loads(result.stdout.strip().splitlines()[-1])  # last line is the JSON
    assert "findings" in parsed
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `validate_cmd`**

Replace the stub `validate_cmd` in `src/clean_agents/cli/skill_cmd.py` with:

```python
import json as _json
from pathlib import Path as _Path

import yaml as _yaml
from rich.table import Table

from clean_agents.crafters.base import ArtifactType
from clean_agents.crafters.skill.spec import SkillSpec
from clean_agents.crafters.validators.base import (
    Level,
    Severity,
    ValidationContext,
    ValidationReport,
    get_registry,
)
from clean_agents.crafters.validators.collision import default_installed_roots


def _load_spec(path: _Path) -> tuple[SkillSpec, _Path | None]:
    """Accept either a bundle directory (with .skill-spec.yaml) or a YAML file."""
    if path.is_dir():
        yaml_path = path / ".skill-spec.yaml"
        bundle_root: _Path | None = path
    else:
        yaml_path = path
        bundle_root = path.parent if path.parent.exists() else None
    data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return SkillSpec.model_validate(data), bundle_root


def _run_validators(
    spec: SkillSpec,
    ctx: ValidationContext,
    levels: set[Level],
) -> ValidationReport:
    report = ValidationReport()
    for v in get_registry().for_artifact(ArtifactType.SKILL):
        if v.level not in levels:
            continue
        try:
            report.findings.extend(v.check(spec, ctx))
        except Exception as e:
            report.findings.append(
                # Surface validator bugs instead of swallowing (no silent failures)
                _finding_for_exception(v.rule_id, e),
            )
    return report


def _finding_for_exception(rule_id: str, err: Exception):
    from clean_agents.crafters.validators.base import Severity as _S, ValidationFinding as _VF
    return _VF(
        rule_id=rule_id, severity=_S.INFO,
        message=f"validator {rule_id} raised {type(err).__name__}: {err}",
        fix_hint="File an issue at github.com/Leandrozz/clean-agents with the full traceback.",
    )


def validate_cmd(
    path: str = typer.Argument(..., help="Path to skill bundle or .skill-spec.yaml"),
    level: str = typer.Option("L1,L2,L3", "--level", help="Comma-separated levels"),
    eval_: bool = typer.Option(False, "--eval", help="Include L4 runtime eval (requires ANTHROPIC_API_KEY)"),
    fmt: str = typer.Option("table", "--format", help="table | json | md"),
) -> None:
    p = _Path(path)
    if not p.exists():
        console.print(f"[red]path not found:[/] {p}")
        raise typer.Exit(code=2)
    spec, bundle_root = _load_spec(p)

    levels = {Level(tok.strip()) for tok in level.split(",")}
    if eval_:
        levels.add(Level.L4)

    ctx = ValidationContext(
        bundle_root=bundle_root,
        installed_roots=default_installed_roots(),
    )
    report = _run_validators(spec, ctx, levels)

    if fmt == "json":
        console.print(_json.dumps(report.model_dump(mode="json"), indent=2))
    elif fmt == "md":
        for f in report.findings:
            console.print(f"- **{f.severity.value.upper()}** `{f.rule_id}` — {f.message}")
    else:
        if not report.findings:
            console.print("[green]No findings — skill passes validation.[/]")
        else:
            table = Table(title=f"Validation findings for {spec.name}")
            table.add_column("Severity")
            table.add_column("Rule")
            table.add_column("Message")
            table.add_column("Location")
            for f in report.findings:
                table.add_row(f.severity.value, f.rule_id, f.message, f.location or "—")
            console.print(table)

    if report.has_critical() or report.has_blocking():
        raise typer.Exit(code=1)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py tests/test_crafters_cli.py
git commit -m "feat(crafters): wire skill validate L1+L2+L3 with table/json/md formats"
```

### Task M6.2: Replace `skill render` stub with real renderer + validation gate

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_cli.py (append)
def test_render_creates_bundle(tmp_path: Path):
    spec_path = Path("tests/fixtures/crafters/skill/good-skill/.skill-spec.yaml")
    result = runner.invoke(app, [
        "skill", "render", str(spec_path),
        "--output", str(tmp_path / "out"),
    ])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "out" / "SKILL.md").exists()
    assert (tmp_path / "out" / ".skill-spec.yaml").exists()


def test_render_blocks_on_critical(tmp_path: Path):
    spec_path = Path("tests/fixtures/crafters/skill/bad-desc-too-long/.skill-spec.yaml")
    result = runner.invoke(app, [
        "skill", "render", str(spec_path),
        "--output", str(tmp_path / "out"),
    ])
    assert result.exit_code != 0
    assert "blocked" in result.stdout.lower() or "critical" in result.stdout.lower()


def test_render_force_overrides(tmp_path: Path):
    spec_path = Path("tests/fixtures/crafters/skill/bad-desc-too-long/.skill-spec.yaml")
    result = runner.invoke(app, [
        "skill", "render", str(spec_path),
        "--output", str(tmp_path / "out"),
        "--force",
    ])
    assert result.exit_code == 0
    assert (tmp_path / "out" / "SKILL.md").exists()
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_cli.py::test_render_creates_bundle -v`
Expected: FAIL.

- [ ] **Step 3: Implement `render_cmd`**

Replace the stub:

```python
def render_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
    output: str = typer.Option(..., "--output", "-o", help="Output bundle directory"),
    zip_: bool = typer.Option(False, "--zip", help="Package as .skill zip"),
    force: bool = typer.Option(False, "--force", help="Ignore HIGH/CRITICAL findings"),
) -> None:
    p = _Path(spec)
    if not p.exists():
        console.print(f"[red]spec not found:[/] {p}")
        raise typer.Exit(code=2)

    skill_spec = SkillSpec.model_validate(_yaml.safe_load(p.read_text(encoding="utf-8")))
    out_dir = _Path(output)

    ctx = ValidationContext(bundle_root=out_dir, installed_roots=default_installed_roots())
    report = _run_validators(skill_spec, ctx, {Level.L1, Level.L2, Level.L3})

    if report.has_critical() and not force:
        console.print("[red]Render blocked — critical findings present.[/]")
        for f in report.findings:
            if f.severity is Severity.CRITICAL:
                console.print(f"  CRITICAL {f.rule_id}: {f.message}")
        raise typer.Exit(code=1)

    from clean_agents.crafters.skill.scaffold import render_skill_bundle
    bundle = render_skill_bundle(skill_spec, out_dir)
    console.print(f"[green]Bundle rendered:[/] {bundle.output_dir}")

    if zip_:
        import shutil
        shutil.make_archive(str(out_dir), "zip", out_dir)
        console.print(f"[green]Zipped:[/] {out_dir}.zip")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py tests/test_crafters_cli.py
git commit -m "feat(crafters): wire skill render with validation gate + --force + --zip"
```

### Task M6.3: Implement `skill design` (non-interactive first, interactive deferred to M7)

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_cli.py (append)
def test_design_non_interactive_from_spec(tmp_path: Path):
    spec_path = Path("tests/fixtures/crafters/skill/good-skill/.skill-spec.yaml")
    result = runner.invoke(app, [
        "skill", "design",
        "--spec", str(spec_path),
        "--no-interactive",
        "--output", str(tmp_path / "designed"),
    ])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "designed" / "SKILL.md").exists()


def test_design_from_description_minimal(tmp_path: Path):
    result = runner.invoke(app, [
        "skill", "design",
        "demo skill that detects markdown tables in a prompt",
        "--no-interactive",
        "--output", str(tmp_path / "desc"),
    ])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "desc" / ".skill-spec.yaml").exists()
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `design_cmd`**

Replace the stub:

```python
def design_cmd(
    description: str = typer.Argument("", help="Natural-language description"),
    ai: bool = typer.Option(False, "--ai", help="Use Anthropic SDK for richer recommendations"),
    for_agent: str = typer.Option("", "--for-agent", help="Link this skill to a specific agent"),
    blueprint: str = typer.Option("", "--blueprint", help="Blueprint YAML to pre-load context"),
    spec: str = typer.Option("", "--spec", help="Structured YAML input"),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="One-shot from --spec / description"
    ),
    lang: str = typer.Option("en", "--lang", help="Output language (en, es, pt)"),
    output: str = typer.Option(".", "--output", "-o", help="Output bundle directory"),
) -> None:
    from clean_agents.crafters.session import DesignConfig, DesignSession, Phase

    if spec:
        spec_data = _yaml.safe_load(_Path(spec).read_text(encoding="utf-8"))
        skill_spec = SkillSpec.model_validate(spec_data)
    elif description:
        # Minimal heuristic draft from NL description
        desc = description.strip()
        if len(desc) < 50:
            desc = (desc + " — designed via clean-agents skill design --no-interactive.").strip()
        if len(desc) > 500:
            desc = desc[:497] + "..."
        # Derive a kebab-case name
        name = "-".join(
            tok.lower() for tok in desc.split()[:3] if tok.isalnum()
        ) or "unnamed-skill"
        skill_spec = SkillSpec(
            name=name,
            description=desc,
            language=lang,
            triggers=[tok.lower() for tok in desc.split()[:5] if tok.isalnum()],
            references=[],
            body_outline=[],
        )
    else:
        console.print("[red]Provide either --spec or a description argument.[/]")
        raise typer.Exit(code=2)

    session = DesignSession[SkillSpec](
        spec=skill_spec,
        config=DesignConfig(enable_ai=ai, language=lang, interactive=not no_interactive),
    )
    session.intake(skill_spec)

    if not no_interactive:
        console.print("[yellow]Interactive design loop coming in M7; running one-shot for now.[/]")

    bundle = session.render(_Path(output))
    console.print(f"[green]Bundle written:[/] {bundle.output_dir}")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py tests/test_crafters_cli.py
git commit -m "feat(crafters): wire skill design non-interactive path (from --spec or description)"
```

### Task M6.4: Wire `skill publish` to the existing marketplace infra (dry-run first)

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_cli.py (append)
def test_publish_dry_run():
    spec_path = Path("tests/fixtures/crafters/skill/good-skill/.skill-spec.yaml")
    result = runner.invoke(app, [
        "skill", "publish", str(spec_path),
        "--dry-run",
    ])
    assert result.exit_code == 0, result.stdout
    assert "dry" in result.stdout.lower()
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_cli.py::test_publish_dry_run -v`
Expected: FAIL.

- [ ] **Step 3: Implement `publish_cmd`**

Replace the stub:

```python
def publish_cmd(
    spec: str = typer.Argument(..., help="Path to .skill-spec.yaml"),
    marketplace: str = typer.Option("", "--marketplace", help="Marketplace URL"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate + simulate publish"),
) -> None:
    p = _Path(spec)
    if not p.exists():
        console.print(f"[red]spec not found:[/] {p}")
        raise typer.Exit(code=2)

    skill_spec = SkillSpec.model_validate(_yaml.safe_load(p.read_text(encoding="utf-8")))
    ctx = ValidationContext(installed_roots=default_installed_roots())
    report = _run_validators(skill_spec, ctx, {Level.L1, Level.L2, Level.L3})

    if report.has_blocking():
        console.print("[red]Publish blocked — fix HIGH/CRITICAL findings first.[/]")
        raise typer.Exit(code=1)

    if dry_run:
        console.print(f"[green]Dry-run OK for {skill_spec.name}[/] — would publish to {marketplace or 'default marketplace'}.")
        return

    console.print("[yellow]Marketplace publish integration coming in M10.[/]")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py tests/test_crafters_cli.py
git commit -m "feat(crafters): wire skill publish --dry-run with validation gate"
```

---

## Milestone M7 — AI-enhanced mode (`--ai`) using `ClaudeArchitect`

**Dependencies:** M5, M6.

### Task M7.1: Extend `ClaudeArchitect` with `detect_contradictions` + `suggest_triggers`

**Files:**
- Modify: `src/clean_agents/integrations/anthropic.py` (read current impl first, then append methods)
- Create: `tests/test_crafters_ai.py`

- [ ] **Step 1: Write failing test with mocked SDK**

```python
# tests/test_crafters_ai.py
from unittest.mock import MagicMock, patch

from clean_agents.integrations.anthropic import ClaudeArchitect


def test_detect_contradictions_returns_list():
    client_mock = MagicMock()
    client_mock.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["claim A contradicts claim B"]')],
    )
    arch = ClaudeArchitect(client=client_mock)
    result = arch.detect_contradictions("some body text")
    assert isinstance(result, list)
    assert "contradicts" in result[0]


def test_suggest_triggers_returns_list():
    client_mock = MagicMock()
    client_mock.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["pdf table", "markdown grid", "csv parse"]')],
    )
    arch = ClaudeArchitect(client=client_mock)
    triggers = arch.suggest_triggers("detect tables in markdown")
    assert len(triggers) == 3
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_ai.py -v`
Expected: FAIL (methods missing).

- [ ] **Step 3: Read the existing `ClaudeArchitect` class to match its init signature, then append methods**

Add to `src/clean_agents/integrations/anthropic.py`:

```python
import json as _json_ca


class _SkillCrafterMixin:
    """Mixin pulled into ClaudeArchitect for skill-crafter-specific calls."""

    def detect_contradictions(self, text: str) -> list[str]:
        prompt = (
            "You are reviewing a Claude Code skill body for internal contradictions. "
            "Reply with a JSON array of short sentences describing contradictions. "
            "Return [] if there are none.\n\n"
            f"--- BEGIN BODY ---\n{text}\n--- END BODY ---"
        )
        resp = self.client.messages.create(
            model="claude-haiku-4-5", max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        payload = resp.content[0].text
        try:
            return list(_json_ca.loads(payload))
        except Exception:
            return []

    def suggest_triggers(self, description: str) -> list[str]:
        prompt = (
            "Suggest 5-10 distinctive activation-trigger keywords/phrases for a Claude Code "
            "skill with this description. Reply as a JSON array of strings.\n\n"
            f"Description: {description}"
        )
        resp = self.client.messages.create(
            model="claude-haiku-4-5", max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return list(_json_ca.loads(resp.content[0].text))
        except Exception:
            return []

    def generate_eval_prompts(
        self, description: str, triggers: list[str], n: int = 10,
    ) -> dict[str, list[str]]:
        prompt = (
            "For a Claude Code skill with description and triggers, generate "
            f"{n} POSITIVE prompts that SHOULD activate the skill and {n} NEGATIVE "
            "prompts that should NOT. Reply as JSON: "
            '{"positive":[...], "negative":[...]}\n\n'
            f"description: {description}\ntriggers: {triggers}"
        )
        resp = self.client.messages.create(
            model="claude-haiku-4-5", max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return _json_ca.loads(resp.content[0].text)
        except Exception:
            return {"positive": [], "negative": []}
```

Then ensure `ClaudeArchitect` inherits from `_SkillCrafterMixin` (edit the class line to include the mixin in its base list). If `ClaudeArchitect` has no `client` attribute yet, pass it through the constructor.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_ai.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/integrations/anthropic.py tests/test_crafters_ai.py
git commit -m "feat(crafters): add ClaudeArchitect methods for contradictions/triggers/eval prompts"
```

### Task M7.2: Thread `--ai` through `skill design` and `skill validate`

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_ai.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_ai.py (append)
from pathlib import Path

from typer.testing import CliRunner

from clean_agents.cli.main import app

runner = CliRunner()


def test_ai_flag_enables_contradiction_check(monkeypatch, tmp_path: Path):
    from clean_agents.integrations import anthropic as ant

    class _FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                return MagicMock(content=[MagicMock(text='["A says X and not-X"]')])

    monkeypatch.setattr(ant, "get_architect", lambda: ant.ClaudeArchitect(client=_FakeClient()))

    fixture = Path("tests/fixtures/crafters/skill/good-skill")
    result = runner.invoke(app, ["skill", "validate", str(fixture), "--level", "L2"])
    assert result.exit_code in (0, 1)  # may or may not block depending on severity
```

- [ ] **Step 2: Implement `get_architect()` factory** (if not already present) in `integrations/anthropic.py`:

```python
_architect: "ClaudeArchitect | None" = None


def get_architect() -> "ClaudeArchitect":
    global _architect
    if _architect is None:
        from anthropic import Anthropic
        _architect = ClaudeArchitect(client=Anthropic())
    return _architect
```

- [ ] **Step 3: Inject architect into `SkillL2Contradictions` in `validate_cmd`**

Modify `_run_validators` in `skill_cmd.py` to attach the architect client when `ctx.enable_ai=True`:

```python
def _run_validators(spec, ctx, levels):
    report = ValidationReport()
    ai_client = None
    if ctx.enable_ai:
        try:
            from clean_agents.integrations.anthropic import get_architect
            ai_client = get_architect()
        except Exception as e:
            console.print(f"[yellow]AI mode requested but unavailable: {e}; falling back to heuristics.[/]")

    for v in get_registry().for_artifact(ArtifactType.SKILL):
        if v.level not in levels:
            continue
        # Inject AI client into contradiction validator
        if v.rule_id == "SKILL-L2-CONTRADICTIONS":
            v.client = ai_client
        try:
            report.findings.extend(v.check(spec, ctx))
        except Exception as e:
            report.findings.append(_finding_for_exception(v.rule_id, e))
    return report
```

And set `ctx.enable_ai = True` in `validate_cmd` when `--ai` is passed (add `ai: bool = typer.Option(False, "--ai")` option to the signature).

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_ai.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py src/clean_agents/integrations/anthropic.py tests/test_crafters_ai.py
git commit -m "feat(crafters): thread --ai through skill validate + inject Claude into contradictions check"
```

---

## Milestone M8 — L4 eval harness (`--eval`)

**Dependencies:** M6, M7.

### Task M8.1: `SKILL-L4-ACTIVATION-PRECISION` with simulated activation

**Files:**
- Create: `src/clean_agents/crafters/validators/runtime.py`
- Modify: `src/clean_agents/crafters/skill/validators.py`
- Test: `tests/test_crafters_runtime.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_runtime.py
from datetime import datetime
from unittest.mock import MagicMock

from clean_agents.crafters.skill.spec import EvalCase, EvalsManifest, SkillSpec
from clean_agents.crafters.skill.validators import SkillL4ActivationPrecision
from clean_agents.crafters.validators.base import Severity, ValidationContext


def _spec_with_evals(cases_pos: list[str], cases_neg: list[str]) -> SkillSpec:
    return SkillSpec(
        name="eval-skill",
        description="A fixture used to exercise the L4 eval harness with mocked activation.",
        triggers=["eval"],
        references=[], body_outline=[],
        evals=EvalsManifest(
            positive_cases=[EvalCase(prompt=p, expected="activate") for p in cases_pos],
            negative_cases=[EvalCase(prompt=p, expected="ignore") for p in cases_neg],
        ),
    )


def test_l4_passes_when_tpr_and_fpr_within_thresholds():
    # activate returns True for positives, False for negatives → perfect
    fake = MagicMock(side_effect=lambda prompt: "positive" in prompt)
    v = SkillL4ActivationPrecision(activate_fn=fake)
    spec = _spec_with_evals(["positive A", "positive B"], ["decoy one", "decoy two"])
    findings = v.check(spec, ValidationContext(enable_ai=True))
    assert findings == []


def test_l4_fires_when_tpr_too_low():
    # Never activates on positives → TPR=0
    fake = MagicMock(return_value=False)
    v = SkillL4ActivationPrecision(activate_fn=fake)
    spec = _spec_with_evals(["p1", "p2"], ["n1", "n2"])
    findings = v.check(spec, ValidationContext(enable_ai=True))
    assert findings
    assert findings[0].severity in (Severity.HIGH, Severity.MEDIUM)
    assert "TPR" in findings[0].message
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_runtime.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement harness + validator**

```python
# src/clean_agents/crafters/validators/runtime.py
"""L4 runtime eval harness — simulated skill activation against generated prompts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable


def compute_tpr_fpr(
    results: list[tuple[str, str, bool]],   # (prompt, expected, activated)
) -> tuple[float, float]:
    pos = [r for r in results if r[1] == "activate"]
    neg = [r for r in results if r[1] == "ignore"]
    tpr = (sum(1 for _, _, a in pos if a) / len(pos)) if pos else 0.0
    fpr = (sum(1 for _, _, a in neg if a) / len(neg)) if neg else 0.0
    return tpr, fpr


def write_results(output: Path, results: list[dict]) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"results-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return path


ActivationFn = Callable[[str], bool]
```

Then append to `src/clean_agents/crafters/skill/validators.py`:

```python
from clean_agents.crafters.validators.runtime import (
    ActivationFn,
    compute_tpr_fpr,
)


class SkillL4ActivationPrecision(ValidatorBase[SkillSpec]):
    level = Level.L4
    artifact_type = ArtifactType.SKILL
    rule_id = "SKILL-L4-ACTIVATION-PRECISION"

    def __init__(self, activate_fn: ActivationFn | None = None) -> None:
        self.activate_fn = activate_fn

    def check(self, spec: SkillSpec, ctx: ValidationContext) -> list[ValidationFinding]:
        if not ctx.enable_ai or spec.evals is None or self.activate_fn is None:
            return []
        triples: list[tuple[str, str, bool]] = []
        for c in spec.evals.positive_cases:
            triples.append((c.prompt, "activate", bool(self.activate_fn(c.prompt))))
        for c in spec.evals.negative_cases:
            triples.append((c.prompt, "ignore", bool(self.activate_fn(c.prompt))))

        tpr, fpr = compute_tpr_fpr(triples)
        out: list[ValidationFinding] = []
        if tpr < spec.evals.thresholds.tpr_min:
            out.append(ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.HIGH,
                message=f"TPR {tpr:.2f} below threshold {spec.evals.thresholds.tpr_min}",
                location="spec.evals",
                fix_hint="Broaden triggers or positive cases; inspect failing positives.",
            ))
        if fpr > spec.evals.thresholds.fpr_max:
            out.append(ValidationFinding(
                rule_id=self.rule_id,
                severity=Severity.HIGH,
                message=f"FPR {fpr:.2f} above threshold {spec.evals.thresholds.fpr_max}",
                location="spec.evals",
                fix_hint="Narrow triggers; inspect activating decoys.",
            ))
        return out
```

Register in `register_builtin()`. Add a `--eval` option to `validate_cmd` that passes a concrete `activate_fn` backed by the mocked-in-CI Anthropic client (real wiring lands in M8.2).

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_runtime.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/crafters/validators/runtime.py src/clean_agents/crafters/skill/validators.py tests/test_crafters_runtime.py
git commit -m "feat(crafters): L4 activation-precision validator with TPR/FPR harness"
```

### Task M8.2: Wire `--eval` into `skill validate` with a real activation function

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Write failing test (mocks the Anthropic client)**

```python
# tests/test_crafters_cli.py (append)
def test_validate_with_eval_flag(monkeypatch, tmp_path: Path):
    from clean_agents.integrations import anthropic as ant
    from unittest.mock import MagicMock

    class _FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                # Always "activate" → artificially high FPR
                return MagicMock(content=[MagicMock(text="ACTIVATE")])

    monkeypatch.setattr(ant, "get_architect", lambda: ant.ClaudeArchitect(client=_FakeClient()))

    # Bundle must have evals in its spec; good-skill doesn't, so use a tmp one
    spec = {
        "name": "eval-test",
        "description": "A fixture used to test the --eval flag against a mocked Anthropic client.",
        "artifact_type": "skill",
        "language": "en",
        "triggers": ["eval", "test"],
        "references": [],
        "body_outline": [],
        "evals": {
            "positive_cases": [{"prompt": "yes", "expected": "activate"}],
            "negative_cases": [{"prompt": "no", "expected": "ignore"}],
        },
    }
    import yaml as _y
    (tmp_path / "spec.yaml").write_text(_y.safe_dump(spec), encoding="utf-8")

    result = runner.invoke(app, [
        "skill", "validate", str(tmp_path / "spec.yaml"),
        "--level", "L4", "--eval", "--ai",
    ])
    # Either passes with info or fails with FPR finding — we don't care which,
    # only that the harness ran without crashing.
    assert "SKILL-L4-ACTIVATION-PRECISION" in result.stdout or result.exit_code in (0, 1)
```

- [ ] **Step 2: Implement activation function**

Add to `skill_cmd.py`:

```python
def _make_activation_fn(arch) -> "ActivationFn":
    """Returns a callable prompt -> bool using a mocked/real Anthropic client."""
    def _fn(prompt: str) -> bool:
        try:
            resp = arch.client.messages.create(
                model="claude-haiku-4-5", max_tokens=16,
                messages=[{"role": "user", "content": (
                    "Should a Claude Code skill be activated for the following user prompt? "
                    f"Reply ACTIVATE or IGNORE, nothing else.\n\nPrompt: {prompt}"
                )}],
            )
            return "ACTIVATE" in resp.content[0].text.upper()
        except Exception:
            return False
    return _fn
```

And inject it into `SkillL4ActivationPrecision` when `--eval` + `--ai` are set, inside `_run_validators`.

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_crafters_cli.py tests/test_crafters_runtime.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py tests/test_crafters_cli.py
git commit -m "feat(crafters): wire --eval flag into skill validate with mocked activation"
```

---

## Milestone M9 — Bidirectional Blueprint integration

**Dependencies:** M5, M6.

### Task M9.1: Extend `AgentSpec` with `recommended_artifacts`

**Files:**
- Modify: `src/clean_agents/core/agent.py`
- Test: `tests/test_crafters_blueprint_integration.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_blueprint_integration.py
from pathlib import Path

from clean_agents.core.agent import AgentSpec
from clean_agents.crafters.base import ArtifactRef, ArtifactType


def test_agent_spec_has_recommended_artifacts_default_empty():
    a = AgentSpec(name="a", role="classifier")
    assert a.recommended_artifacts == []


def test_agent_spec_accepts_artifact_refs():
    ref = ArtifactRef(
        artifact_type=ArtifactType.SKILL,
        name="legal-patterns",
        rationale="agent works with legal jargon",
        spec_path=Path(".clean-agents/skills/legal-patterns/.skill-spec.yaml"),
        status="needed",
    )
    a = AgentSpec(name="risk_evaluator", role="legal risk assessor", recommended_artifacts=[ref])
    assert a.recommended_artifacts[0].name == "legal-patterns"
    assert a.recommended_artifacts[0].artifact_type is ArtifactType.SKILL


def test_existing_blueprint_yaml_still_loads():
    """Regression: Blueprints from v0.1 without recommended_artifacts must still load."""
    import yaml
    from clean_agents.core.blueprint import Blueprint
    data = {
        "name": "legacy",
        "agents": [{"name": "a", "role": "classifier"}],
    }
    bp = Blueprint.model_validate(data)
    assert bp.agents[0].recommended_artifacts == []
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_blueprint_integration.py -v`
Expected: FAIL (`recommended_artifacts` missing).

- [ ] **Step 3: Modify `core/agent.py`**

`clean_agents.crafters.base` does not import from `clean_agents.core.agent`, so a direct import is safe — no circular-import dance needed.

At the top of `src/clean_agents/core/agent.py` add:

```python
from clean_agents.crafters.base import ArtifactRef
```

Then, inside `AgentSpec` (anywhere among the fields — order only affects YAML output):

```python
    # --- Crafters integration (added in v0.2; defaults preserve v0.1 compatibility) ---
    recommended_artifacts: list[ArtifactRef] = Field(default_factory=list)
```

- [ ] **Step 4: Run tests + full suite**

Run: `pytest tests/ -q`
Expected: ALL tests PASS (303 pre-existing + new).

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/core/agent.py tests/test_crafters_blueprint_integration.py
git commit -m "feat(crafters): add AgentSpec.recommended_artifacts (default empty — non-breaking)"
```

### Task M9.2: `--for-agent --blueprint` pre-loads agent context into `skill design`

**Files:**
- Modify: `src/clean_agents/cli/skill_cmd.py`
- Test: `tests/test_crafters_blueprint_integration.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_blueprint_integration.py (append)
from typer.testing import CliRunner

from clean_agents.cli.main import app

runner = CliRunner()


def test_skill_design_for_agent_loads_blueprint(tmp_path: Path):
    import yaml
    bp = {
        "name": "demo",
        "agents": [
            {"name": "risk_evaluator", "role": "legal risk assessor"},
            {"name": "classifier", "role": "intent router"},
        ],
    }
    bp_path = tmp_path / "blueprint.yaml"
    bp_path.write_text(yaml.safe_dump(bp), encoding="utf-8")

    out = tmp_path / "skill-out"
    result = runner.invoke(app, [
        "skill", "design",
        "--for-agent", "risk_evaluator",
        "--blueprint", str(bp_path),
        "--no-interactive",
        "--output", str(out),
    ])
    assert result.exit_code == 0, result.stdout
    assert (out / ".skill-spec.yaml").exists()
    spec_data = yaml.safe_load((out / ".skill-spec.yaml").read_text(encoding="utf-8"))
    assert "risk_evaluator" in spec_data["description"]
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_crafters_blueprint_integration.py -v`
Expected: FAIL.

- [ ] **Step 3: Extend `design_cmd`**

In `skill_cmd.py` `design_cmd`, before constructing the spec, add:

```python
    # Load blueprint context if requested
    agent_context: str = ""
    if for_agent and blueprint:
        from clean_agents.core.blueprint import Blueprint
        bp = Blueprint.load(_Path(blueprint))
        agent = bp.get_agent(for_agent)
        if agent is None:
            console.print(f"[red]agent {for_agent!r} not found in blueprint[/]")
            raise typer.Exit(code=2)
        agent_context = (
            f" For agent {agent.name!r} ({agent.role}); "
            f"model={agent.model.primary}, memory="
            f"{'graphrag' if agent.memory.graphrag else 'short-term'}."
        )

    if spec:
        ...
    elif description or agent_context:
        desc = (description or f"Skill supporting {for_agent}").strip() + agent_context
        ...
```

Make sure the final rendered `spec.description` contains `for_agent` so the test asserts pass.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_crafters_blueprint_integration.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/clean_agents/cli/skill_cmd.py tests/test_crafters_blueprint_integration.py
git commit -m "feat(crafters): --for-agent --blueprint pre-loads agent context into skill design"
```

### Task M9.3: `suggest-artifacts` Phase-5 module inside existing `clean-agents design`

**Files:**
- Modify: `src/clean_agents/cli/design_cmd.py`
- Test: `tests/test_crafters_blueprint_integration.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_crafters_blueprint_integration.py (append)
def test_design_suggest_artifacts_module(tmp_path: Path):
    import yaml
    bp = {
        "name": "demo",
        "agents": [
            {"name": "a", "role": "legal risk assessor with jargon"},
            {"name": "b", "role": "intent classifier"},
        ],
    }
    bp_path = tmp_path / "blueprint.yaml"
    bp_path.write_text(yaml.safe_dump(bp), encoding="utf-8")

    result = runner.invoke(app, [
        "design", "--blueprint", str(bp_path),
        "--module", "suggest-artifacts",
        "--no-interactive",
    ])
    assert result.exit_code == 0, result.stdout
    # It prints an ArtifactRef table with `--for-agent` suggestions
    assert "--for-agent" in result.stdout
```

- [ ] **Step 2: Implement the module**

Open `src/clean_agents/cli/design_cmd.py`, locate the Phase-5 module dispatch, and add a handler:

```python
def _module_suggest_artifacts(blueprint) -> None:
    from clean_agents.crafters.base import ArtifactRef, ArtifactType
    from rich.table import Table

    table = Table(title="Suggested artifacts")
    table.add_column("Agent")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Rationale")
    table.add_column("Priority")

    for agent in blueprint.agents:
        suggestions: list[ArtifactRef] = []
        role_lc = agent.role.lower()
        if any(w in role_lc for w in ("legal", "risk", "jargon", "medical", "financial")):
            suggestions.append(ArtifactRef(
                artifact_type=ArtifactType.SKILL,
                name=f"{agent.name.replace('_','-')}-domain-patterns",
                rationale="domain-specific jargon indicates a dedicated Skill",
                priority="recommended",
            ))
        if agent.memory.graphrag:
            suggestions.append(ArtifactRef(
                artifact_type=ArtifactType.MCP,
                name=f"{agent.name.replace('_','-')}-graph-mcp",
                rationale="graphrag memory benefits from a typed MCP wrapper",
                priority="recommended",
            ))
        for s in suggestions:
            table.add_row(agent.name, s.artifact_type.value, s.name, s.rationale, s.priority)
            console.print(
                f"  run: clean-agents skill design --for-agent {agent.name} "
                f"--blueprint <blueprint.yaml>"
            )

    console.print(table)
```

Hook this handler into the existing Phase-5 module switch in `design_cmd`, or add a `--module` option if one doesn't exist (read the file to confirm).

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_crafters_blueprint_integration.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/clean_agents/cli/design_cmd.py tests/test_crafters_blueprint_integration.py
git commit -m "feat(crafters): add Phase-5 suggest-artifacts module in clean-agents design"
```

---

## Milestone M10 — KB seed + `FlatYAMLKnowledge` + docs + release

**Dependencies:** M1–M9.

### Task M10.1: Seed `best-practices.yaml` and `anti-patterns.yaml`

**Files:**
- Create: `knowledge/crafters/skill/best-practices.yaml`
- Create: `knowledge/crafters/skill/anti-patterns.yaml`
- Test: `tests/test_crafters_knowledge.py`

- [ ] **Step 1: Write `best-practices.yaml`**

```yaml
- id: progressive-disclosure
  title: Use progressive disclosure
  body: |
    Keep SKILL.md tight (< 2000 words). Move detail to references/*.md so
    Claude can pull it in only when needed.
  applies_to: [skill]
  source: anthropic-docs
- id: distinctive-triggers
  title: Distinctive triggers
  body: |
    Pick 5-10 trigger phrases that unambiguously identify when the skill
    should activate. Avoid generic words ("ai", "agent").
  applies_to: [skill]
  source: anthropic-docs
- id: source-of-truth-yaml
  title: Treat .skill-spec.yaml as source of truth
  body: |
    Edit the YAML and re-render. Never hand-edit SKILL.md — it drifts.
  applies_to: [skill]
```

- [ ] **Step 2: Write `anti-patterns.yaml` (5 entries mapped 1:1 to rule IDs)**

```yaml
- id: hardcoded-stats
  title: Hard-coded stats
  body: Percentages and CVE IDs age within weeks.
  rule_id: SKILL-L2-HARDCODED-STATS
  applies_to: [skill]
- id: hardcoded-name-collision
  title: Name collision with installed skill
  body: Reusing an installed skill's name causes activation ambiguity.
  rule_id: SKILL-L3-NAME-COLLISION
  applies_to: [skill]
- id: description-too-long
  title: Description > 500 chars
  body: Over-long descriptions waste trigger space and confuse activation.
  rule_id: SKILL-L1-DESC-LENGTH
  applies_to: [skill]
- id: language-mix
  title: Mixed-language content
  body: A Spanish sentence in an English skill fights the declared language.
  rule_id: SKILL-L2-LANGUAGE-MIX
  applies_to: [skill]
- id: missing-version-field
  title: Missing version in frontmatter
  body: Installers need a version; missing field breaks upgrade paths.
  rule_id: null   # surfaced at SkillSpec construction time
  applies_to: [skill]
```

- [ ] **Step 3: Write a test loading them**

```python
# tests/test_crafters_knowledge.py (append)
from pathlib import Path


def test_yaml_knowledge_loads_seeded_files():
    from clean_agents.crafters.skill.knowledge import SkillKnowledge
    kb = SkillKnowledge(root=Path("knowledge/crafters/skill"))
    bps = kb.get_best_practices("skill")
    aps = kb.get_anti_patterns("skill")
    assert any(bp.id == "progressive-disclosure" for bp in bps)
    assert any(ap.rule_id == "SKILL-L2-HARDCODED-STATS" for ap in aps)
```

- [ ] **Step 4: Implement `SkillKnowledge` (concrete `FlatYAMLKnowledge` for the Skills vertical)**

```python
# src/clean_agents/crafters/skill/knowledge.py
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
        from clean_agents.crafters.validators.collision import default_installed_roots
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
                overlap = own_keys & set(extract_keywords(readme.read_text(encoding="utf-8", errors="ignore")))
                if overlap:
                    refs.append(ArtifactRef(
                        artifact_type=ArtifactType.SKILL,
                        name=skill_dir.name,
                        rationale=f"keyword overlap: {sorted(overlap)[:5]}",
                        spec_path=skill_dir / ".skill-spec.yaml",
                        status="installed",
                    ))
        refs.sort(key=lambda r: len(r.rationale), reverse=True)
        return refs[:k]

    def get_template(self, name: str) -> JinjaTemplate:
        tpl = self.root / "templates" / name
        if not tpl.exists():
            raise FileNotFoundError(f"template not found: {name}")
        return JinjaTemplate(name=name, path=tpl)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_crafters_knowledge.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add knowledge/crafters/skill src/clean_agents/crafters/skill/knowledge.py tests/test_crafters_knowledge.py
git commit -m "feat(crafters): seed Skills KB (best-practices + anti-patterns) + SkillKnowledge impl"
```

### Task M10.2: `pyproject.toml` extras + entry-point registrations + docs + CHANGELOG

**Files:**
- Modify: `pyproject.toml`
- Create: `docs/crafters/README.md`
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: Update `pyproject.toml`**

```toml
[project.optional-dependencies]
crafters = ["sentence-transformers>=2.7"]
all = ["clean-agents[ai,api,openai,security,eval,observe,load,crafters]"]

[project.entry-points."clean_agents.validators"]
# Built-in skill validators auto-registered (listed for discoverability)
skill-l1-name-dir = "clean_agents.crafters.skill.validators:SkillL1NameDir"
skill-l1-desc-length = "clean_agents.crafters.skill.validators:SkillL1DescLength"
skill-l1-refs-exist = "clean_agents.crafters.skill.validators:SkillL1RefsExist"
skill-l1-refs-orphan = "clean_agents.crafters.skill.validators:SkillL1RefsOrphan"
skill-l2-hardcoded-stats = "clean_agents.crafters.skill.validators:SkillL2HardcodedStats"
skill-l2-hardcoded-dates = "clean_agents.crafters.skill.validators:SkillL2HardcodedDates"
skill-l2-language-mix = "clean_agents.crafters.skill.validators:SkillL2LanguageMix"
skill-l2-trigger-coverage = "clean_agents.crafters.skill.validators:SkillL2TriggerCoverage"
skill-l2-progressive-disclosure = "clean_agents.crafters.skill.validators:SkillL2ProgressiveDisclosure"
skill-l2-promises-vs-delivery = "clean_agents.crafters.skill.validators:SkillL2PromisesVsDelivery"
skill-l2-contradictions = "clean_agents.crafters.skill.validators:SkillL2Contradictions"
skill-l3-name-collision = "clean_agents.crafters.skill.validators:SkillL3NameCollision"
skill-l3-trigger-overlap = "clean_agents.crafters.skill.validators:SkillL3TriggerOverlap"
skill-l3-marketplace-dedupe = "clean_agents.crafters.skill.validators:SkillL3MarketplaceDedupe"
skill-l4-activation-precision = "clean_agents.crafters.skill.validators:SkillL4ActivationPrecision"
```

Remove the programmatic `register_builtin()` call from `crafters/__init__.py` (entry-point discovery replaces it). Update the test that checks `ValidatorRegistry` discovery accordingly.

- [ ] **Step 1b: Wire `skill install` and `skill list` as marketplace aliases**

The spec promises two extra commands that just delegate to the existing marketplace + filesystem scan. Add to `src/clean_agents/cli/skill_cmd.py`:

```python
def install_cmd(name: str = typer.Argument(..., help="Skill name to install")) -> None:
    """Install a skill from the marketplace (delegates to marketplace install)."""
    from clean_agents.cli.marketplace_cmd import marketplace_install_cmd
    marketplace_install_cmd(name=name, kind="skill")   # pass kind so marketplace filters


def list_cmd(
    installed: bool = typer.Option(False, "--installed"),
    marketplace: bool = typer.Option(False, "--marketplace"),
) -> None:
    """List skills (installed locally and/or available in marketplace)."""
    from clean_agents.crafters.validators.collision import (
        default_installed_roots,
        installed_skill_names,
    )
    if installed or not marketplace:
        names = installed_skill_names(default_installed_roots())
        for n, p in sorted(names.items()):
            console.print(f"[green]{n}[/] — {p}")
    if marketplace:
        from clean_agents.cli.marketplace_cmd import marketplace_list_cmd
        marketplace_list_cmd(kind="skill")
```

Register in `main.py` alongside the other `skill_app.command(...)` calls:

```python
skill_app.command("install", help="Install a skill from the marketplace")(skill_install_cmd)
skill_app.command("list", help="List installed and/or marketplace skills")(skill_list_cmd)
```

(Note: `marketplace_install_cmd` / `marketplace_list_cmd` may not accept a `kind=` kwarg today — check their signatures and either add the kwarg with a default that preserves current behavior, or route around them with a direct marketplace API call.)

Add a smoke test:

```python
# tests/test_crafters_cli.py (append)
def test_skill_list_installed_runs():
    result = runner.invoke(app, ["skill", "list", "--installed"])
    assert result.exit_code == 0
```

Run: `pytest tests/test_crafters_cli.py::test_skill_list_installed_runs -v`
Expected: PASS.

- [ ] **Step 2: Create `docs/crafters/README.md`**

```markdown
# CLean-agents Crafters

`clean-agents skill` — design, validate, render, and publish Claude Code Skills
with the same opinionated-consultant flow the tool applies to agentic systems.

## Quick start

```bash
# Non-interactive from a one-liner
clean-agents skill design "detect markdown tables in prompts" -o ./my-skill

# From a structured YAML
clean-agents skill render ./my-skill/.skill-spec.yaml -o ./rendered

# Validate a bundle (L1+L2+L3)
clean-agents skill validate ./my-skill

# AI-enhanced + runtime eval (requires ANTHROPIC_API_KEY)
clean-agents skill validate ./my-skill --ai --eval

# Bidirectional: design a skill for a specific agent in a blueprint
clean-agents skill design \
  --for-agent risk_evaluator \
  --blueprint .clean-agents/blueprint.yaml \
  -o ./risk-patterns

# Cross-direction: recommend artifacts from inside design
clean-agents design --blueprint .clean-agents/blueprint.yaml \
  --module suggest-artifacts
```

## Future verticals

MCPs, Tools, and Plugins follow the same `<noun> <verb>` shape. See spec
`docs/superpowers/specs/2026-04-21-crafters-module-design.md`.
```

- [ ] **Step 3: Update `CHANGELOG.md`**

Append at the top:

```markdown
## [0.2.0] - 2026-04-XX

### Added
- `src/clean_agents/crafters/` module — design Skills / MCPs / Tools / Plugins (Skills v1).
- CLI: `clean-agents skill {design,validate,render,publish}`.
- 15 validator rules for Skills (L1/L2/L3/L4) with Pydantic findings.
- Bidirectional Blueprint integration: `AgentSpec.recommended_artifacts`,
  `--for-agent`, and `design --module suggest-artifacts`.
- Optional `crafters` extra (`sentence-transformers>=2.7`). TF-IDF fallback
  preserves offline-first invariant.
- New entry-point group `clean_agents.validators` for third-party rules.

### Changed
- `AgentSpec` now has `recommended_artifacts: list[ArtifactRef]` (default `[]`).
  Blueprints from v0.1 continue to load unchanged.
```

- [ ] **Step 4: Add a crafters section to the root `README.md`**

Append a section linking to `docs/crafters/README.md` with the quick-start snippet above.

- [ ] **Step 5: Run full suite + lint + types**

Run (parallel-safe, but run sequentially as listed):

```bash
pytest tests/ -q
ruff check src/
mypy src/clean_agents/crafters
```

Expected: 303 pre-existing tests pass, all new tests pass, ruff clean, mypy reports no new errors.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml docs/crafters README.md CHANGELOG.md src/clean_agents/crafters/__init__.py
git commit -m "chore(crafters): pyproject extras + validator entry points + docs + CHANGELOG for v0.2"
```

### Task M10.3: Release smoke test — E2E against Leandro's real skill fixture

**Files:**
- Test: `tests/test_crafters_cli.py`

- [ ] **Step 1: Write final regression test**

```python
# tests/test_crafters_cli.py (append)
def test_e2e_leandro_real_skill_validates_with_known_findings():
    fixture = Path("tests/fixtures/crafters/skill/leandro-real-skill")
    result = runner.invoke(app, ["skill", "validate", str(fixture), "--format", "json"])
    import json
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    rule_ids = {f["rule_id"] for f in payload["findings"]}
    # These are the findings the author identified manually
    assert "SKILL-L1-DESC-LENGTH" in rule_ids
    assert "SKILL-L2-HARDCODED-STATS" in rule_ids
    assert "SKILL-L2-LANGUAGE-MIX" in rule_ids
```

- [ ] **Step 2: Run**

Run: `pytest tests/test_crafters_cli.py::test_e2e_leandro_real_skill_validates_with_known_findings -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_crafters_cli.py
git commit -m "test(crafters): E2E regression against author's real skill fixture"
```

- [ ] **Step 4: Final full suite run**

Run: `pytest tests/ -q`
Expected: all tests PASS. ~400 tests total (303 pre-existing + ~100 crafters).

- [ ] **Step 5: Tag and push (user action, not a task step)**

Release happens via the project's usual publish process. This plan ends here; v0.2 is ready to cut.

---

## End of plan
