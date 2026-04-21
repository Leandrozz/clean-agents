# Crafters Module — Design Spec

**Status**: Draft (pending user review)
**Date**: 2026-04-21
**Author**: Leandro (leansroasas@gmail.com)
**Target release**: CLean-agents v0.2 (v1 of crafters = Skills vertical)

---

## TL;DR

Add a new section to CLean-agents — **`crafters/`** — that brings the same "opinionated architecture consultant" flow to four artifact types: **Skills**, **MCPs**, **Tools**, and **Plugins** (in that delivery order). Ships a unified `ArtifactSpec` abstraction + reusable `DesignSession[T]` engine + 4-level validator pipeline (structural → semantic → cross-artifact collision → runtime eval), with **Skills as the v1 delivery**. Bidirectional integration with the existing agent-system Blueprint enables two-way recommendation: designing an agent can suggest skills/MCPs/tools it needs, and designing an artifact can inherit context from a blueprint agent.

## Motivation

CLean-agents currently excels at designing agentic **systems** (agents, orchestration, memory, guardrails). But the artifacts that power those systems — Claude Code skills, MCP servers, agent tools, plugin bundles — are designed by hand, without the same evidence-based consultant approach. This module closes that gap.

The project author personally experienced a representative pain during this very session: installing a self-authored skill surfaced a name collision, hardcoded stats, a description >500 chars, and a bilingual Phase-5 quote. Every one of these is mechanically detectable. That pain is the v1 requirements spec.

Additionally, the four artifact types form a natural hierarchy (Plugin contains Skills + MCPs + Commands + Hooks + Agents; MCP exposes Tools; Agent uses Tools) — strong signal that a unified abstraction pays off.

## Scope decisions (closed)

Decided via Q&A during brainstorming (2026-04-21):

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Hybrid pragmatic architecture** (C): ~20% upfront shared abstraction, 80% per-vertical implementation | Avoids both premature abstraction and copy-paste debt |
| 2 | **Full bundle output** (C): `.skill-spec.yaml` + `SKILL.md` + `references/` scaffolds + `evals/` template + optional `.skill` zip + validation report | Matches the value that the project author would have gotten if it had existed 20 min before he built his own skill by hand |
| 3 | **Bidirectional optional integration** with Blueprint (B): artifacts live in separate files, mutual recommendation flow via `--for-agent` flag and new `suggest-artifacts` Phase 5 module | Preserves simple standalone case, unlocks power case, aligns with meta-agent direction |
| 4 | **Delivery order** (B): Skills → MCPs → Tools → Plugins | Skills = freshest context; MCPs = standardized protocol, easiest KB; Tools = leaf artifacts building on MCP learnings; Plugins = aggregator, requires all others |
| 5 | **Validator depth** (C): L1 structural + L2 semantic + L3 cross-artifact collision (always-on) + L4 runtime eval (opt-in `--eval`); L5 adversarial deferred to parallel `skill-shield` module | Max differentiation without scope explosion |

## Architecture

### Module layout

```
src/clean_agents/crafters/
├── base.py                # ArtifactSpec (Pydantic base), ArtifactType enum
├── session.py             # DesignSession[T] engine (5-phase, reusable)
├── knowledge.py           # KnowledgeBase interface + FlatYAMLKnowledge impl
├── renderer.py            # Bundle renderer (Jinja2-based)
├── validators/
│   ├── base.py            # ValidatorBase, ValidationResult, Severity, Registry
│   ├── structural.py      # L1 shared checks
│   ├── semantic.py        # L2 shared checks (language-aware)
│   ├── collision.py       # L3 cross-artifact scanner
│   └── runtime.py         # L4 eval harness (opt-in, uses Anthropic SDK)
├── skill/                 # ← v1 delivery
│   ├── spec.py            # SkillSpec(ArtifactSpec)
│   ├── knowledge.py       # SkillKnowledge (anti-patterns, best practices)
│   ├── validators.py      # Skill-specific L1/L2/L3 rules
│   ├── scaffold.py        # Bundle generation logic
│   └── templates/         # Jinja2 partials
├── mcp/                   # ← v2
├── tool/                  # ← v3
└── plugin/                # ← v4 (aggregator)
```

### Data model

```python
class ArtifactType(str, Enum):
    SKILL = "skill"
    MCP = "mcp"
    TOOL = "tool"
    PLUGIN = "plugin"

class ArtifactSpec(BaseModel):
    # Shared across all four verticals
    name: str
    version: str = "0.1.0"
    description: str
    artifact_type: ArtifactType
    author: str | None = None
    language: str = "en"                    # ISO 639-1 code; validated at construction
    license: str = "MIT"
    created_at: datetime

    # Traceability (enables future meta-agent)
    source: Literal["human", "agent", "blueprint"] = "human"
    blueprint_ref: Path | None = None
```

Vertical-specific subclasses:

```python
class SkillSpec(ArtifactSpec):
    artifact_type: Literal[ArtifactType.SKILL] = ArtifactType.SKILL
    triggers: list[str]                     # keywords extracted from description
    references: list[ReferenceFile]         # progressive-disclosure file scaffolds
    evals: EvalsManifest | None = None
    body_outline: list[SkillSection]        # SKILL.md structure before render
    bundle_format: Literal["dir", "zip"] = "dir"

class ReferenceFile(BaseModel):
    path: Path                              # relative to bundle root, e.g. "references/taxonomy.md"
    topic: str                              # one-line purpose
    outline: list[str]                      # section headings to scaffold into the file
    mentioned_in: list[str] = []            # anchor slugs in SKILL.md that cite this file;
                                            # used by L1-REFS-ORPHAN validator and by auto-update
                                            # when SKILL.md sections are renamed

class EvalsManifest(BaseModel):
    positive_cases: list[EvalCase]          # should trigger skill
    negative_cases: list[EvalCase]          # should NOT trigger skill
    thresholds: EvalThresholds              # TPR >= 0.8, FPR <= 0.2 default
```

Future: `MCPSpec`, `ToolSpec`, `PluginSpec` follow the same pattern.

**Non-breaking extension to existing `AgentSpec`**:

```python
class AgentSpec(BaseModel):
    # ...existing fields unchanged...
    recommended_artifacts: list[ArtifactRef] = []    # NEW, default empty

class ArtifactRef(BaseModel):
    artifact_type: ArtifactType
    name: str
    rationale: str
    spec_path: Path | None
    status: Literal["needed", "designed", "installed"]
    priority: Literal["critical", "recommended", "nice-to-have"]
```

Blueprints v1/v2 without `recommended_artifacts` continue to work — new field defaults to empty list.

## DesignSession engine

Generic, type-parametrized, reusable across all four verticals:

```python
class DesignSession(BaseModel, Generic[T: ArtifactSpec]):
    session_id: UUID
    phase: Phase  # INTAKE | RECOMMEND | DEEP_DIVE | BUNDLE | ITERATE | MODULES
    spec: T
    history: list[Turn]
    validation_state: ValidationReport | None
    config: DesignConfig

    def intake(self, input: str | T) -> Recommendation: ...     # Phase 0 → 1
    def answer(self, question_id: str, answer: Any) -> Delta: ...# Phase 2
    def render(self, output_dir: Path) -> Bundle: ...            # Phase 3
    def iterate(self, edits: dict) -> CascadeReport: ...         # Phase 4
    def module(self, name: str, **kwargs) -> ModuleResult: ...   # Phase 5

    # Persistence (resumable sessions)
    def save(self, path: Path) -> None: ...
    @classmethod
    def load(cls, path: Path) -> "DesignSession[T]": ...
```

### 5-phase flow (mirrors existing `clean-agents design`)

| Phase | Skills-specific behavior |
|-------|--------------------------|
| **0. Intake** | Accepts NL prose OR partial `SkillSpec` YAML. If launched with `--for-agent X --blueprint PATH`, pre-loads agent context from blueprint. |
| **1. Recommend** | Proposes tuned description (length + distinctive triggers), body/references structure, initial draft. Runs L1+L2+L3 opportunistically; findings feed into the recommendation as evidence. |
| **2. Deep dive** | 2–3 targeted questions per turn: positive/negative trigger patterns, scope per reference file, eval cases, dedicated anti-collision drill-down. |
| **3. Bundle** | Full render: `SKILL.md` + `references/*.md` scaffolds + `evals/evals.json` + optional `.skill` zip. Full L1+L2+L3 validation report. |
| **4. Iterate** | User edits; cascade calculator recomputes dependent fields (e.g., shortening description → re-measure trigger coverage). |
| **5. Modules** | On-demand: `eval-pack` (L4 runtime), `publish` (marketplace), `convert-to-plugin` (wrap skill in plugin), `dedupe-report` (vs installed skills). |

### Three key engine properties

1. **Two intake modes from day 1** — prose (human) and structured `ArtifactSpec` (SDK/future meta-agent). API never assumes a human.
2. **Non-rigid phases** — engine decides next action by spec completeness, not fixed order. Complete YAML on intake → jump directly to Phase 3.
3. **AI / heuristic duality** — `--ai` uses Anthropic SDK for enriched recommendations and L2-contradictions detection; without flag, heuristics + local KB. Core **always works offline** (CLean-agents invariant).

### Tech debt incurred (intentional)

The existing `clean-agents design` (Blueprint flow) is **not refactored** to share this engine in v1. Engine is designed so a future refactor is viable, but explicit out-of-scope for v1.

## Validator engine

Registry-pattern with self-registering Pydantic-typed rules, extensible via existing `clean_agents.plugins` entry points.

```python
class Severity(str, Enum):
    CRITICAL, HIGH, MEDIUM, LOW, INFO

class ValidationFinding(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    location: str | None          # "SKILL.md:42" or "spec.description"
    fix_hint: str | None
    auto_fixable: bool            # enables future --fix

class ValidatorBase(ABC, Generic[T: ArtifactSpec]):
    level: Level                  # L1 | L2 | L3 | L4
    artifact_type: ArtifactType
    rule_id: str
    def check(self, spec: T, ctx: ValidationContext) -> list[Finding]: ...

registry = ValidatorRegistry()
```

### Rule catalog for Skills (v1)

Rules are derived directly from the author's own skill review findings:

| Rule ID | Level | Detects |
|---------|-------|---------|
| `SKILL-L1-NAME-DIR` | L1 | `name:` does not match parent directory |
| `SKILL-L1-DESC-LENGTH` | L1 | description outside [50, 500] chars |
| `SKILL-L1-REFS-EXIST` | L1 | file mentioned in `references[]` missing from disk |
| `SKILL-L1-REFS-ORPHAN` | L1 | file in `references/` not mentioned in SKILL.md |
| `SKILL-L2-HARDCODED-STATS` | L2 | regex for `\d+\.\d+%`, `CVE-\d{4}-\d+`, "paper de \d{4}" |
| `SKILL-L2-HARDCODED-DATES` | L2 | specific years/dates that age poorly |
| `SKILL-L2-LANGUAGE-MIX` | L2 | block in a different language than the declared `language` field |
| `SKILL-L2-TRIGGER-COVERAGE` | L2 | description keywords ∩ TRIGGERS-list < 80% |
| `SKILL-L2-PROGRESSIVE-DISCLOSURE` | L2 | SKILL.md > 2000 words with empty `references/` |
| `SKILL-L2-PROMISES-VS-DELIVERY` | L2 | reference cited in SKILL.md but file is stub/empty |
| `SKILL-L2-CONTRADICTIONS` | L2 | requires `--ai`: internal semantic contradictions |
| `SKILL-L3-NAME-COLLISION` | L3 | duplicate in `~/.claude/skills/` + `<project>/.claude/skills/` + installed plugins |
| `SKILL-L3-TRIGGER-OVERLAP` | L3 | >60% keyword overlap with already-installed skill |
| `SKILL-L3-MARKETPLACE-DEDUPE` | L3 | opt-in: query marketplace for redundancy with published skills |
| `SKILL-L4-ACTIVATION-PRECISION` | L4 | eval harness: TPR ≥ 0.8 / FPR ≤ 0.2 against generated prompt set |

### L4 eval harness (opt-in)

1. Extract TRIGGERS + implicit positive cases from description
2. Generate (via `--ai`) N prompts that **should** trigger + N decoy prompts that should **not**
3. Simulate skill activation (inject SKILL.md as system prompt, query Claude)
4. Report TPR/FPR vs thresholds + table of failed edge cases
5. Output: `evals/results-<timestamp>.json` + severity according to thresholds

### Severity → action mapping

- **Critical** → blocks `render()` and `publish()`
- **High** → blocks unless `--force`, prominent warning
- **Medium** → non-blocking warning
- **Low / Info** → verbose report only

### Integration with DesignSession

- **Phase 1** runs L1+L2 opportunistically on the draft; findings feed into the recommendation as evidence
- **Phase 3** runs L1+L2+L3 full sweep; blocks bundle on any Critical finding
- **Phase 5** module `eval-pack` runs L4
- **CLI standalone**: `clean-agents skill validate PATH [--level L1,L2,L3] [--eval]` validates any existing skill (including the author's own, as an integration test)

### Extensibility

Third parties register custom validators via a new entry-point group `clean_agents.validators` (distinct from the existing `clean_agents.plugins` group to keep discovery cheap and avoid loading the full plugin machinery just to validate):

```toml
[project.entry-points."clean_agents.validators"]
acme-pii-check = "acme_validators:PIIValidator"
```

Entry-point classes must inherit from `ValidatorBase[T]`; the registry picks them up at startup and merges them with built-in rules. Example use case: corporate-specific PII detection, internal style rules, license header enforcement.

## Bundle renderer and CLI surface

### Output layout

```
<skill-name>/
├── SKILL.md                    # Rendered: YAML frontmatter + body from spec
├── references/
│   └── <ref-topic>.md          # Scaffold with pre-populated outline
├── evals/
│   └── evals.json              # Template with cases per TRIGGER
├── README.md                   # Auto-generated from spec metadata
├── .skill-spec.yaml            # ← SOURCE OF TRUTH (round-trip friendly)
└── <skill-name>.skill          # Optional if --zip
```

**Source-of-truth decision**: `.skill-spec.yaml` is authoritative. `SKILL.md` is regenerated from the spec. Enables:
- Clean version control (semantic diffs, not markdown diffs)
- Round-trip edit workflow (edit YAML → `skill render` regenerates all)
- Future meta-agent consumes/produces YAML only
- Idempotent re-validation

**Stack**: Jinja2 templates at `src/clean_agents/crafters/skill/templates/` (Jinja2 already in core deps).

### CLI surface

Follows existing `<noun> <verb>` convention:

```bash
# Skills (v1)
clean-agents skill design [DESC]
  --ai                                  # Anthropic SDK enhanced
  --for-agent NAME --blueprint PATH     # integration B: pre-load from blueprint
  --spec PATH                           # structured YAML input
  --no-interactive                      # one-shot from --desc/--spec
  --lang {en,es,pt}

clean-agents skill validate PATH
  --level L1,L2,L3                      # default: L1,L2,L3
  --eval                                # activates L4 (requires ANTHROPIC_API_KEY)
  --format {table,json,md}
  --fix                                 # auto-fix findings where auto_fixable=True

clean-agents skill render SPEC_YAML
  --output DIR
  --zip                                 # package as .skill
  --force                               # ignore high/critical findings

clean-agents skill publish SPEC_YAML
  --marketplace URL
  --dry-run

clean-agents skill install NAME         # extends existing marketplace
clean-agents skill list --installed --marketplace
```

### Bidirectional Blueprint integration

**Agent → Artifact**:

```bash
clean-agents design
  # Phase 5 new on-demand module: "suggest-artifacts"
  # Analyzes each agent of the blueprint; recommends skills/MCPs/tools;
  # offers to design non-existing ones. Output: list of --for-agent calls.
```

**Artifact → Agent**:

```bash
clean-agents skill design --for-agent risk_evaluator --blueprint .clean-agents/blueprint.yaml
  # Pre-loads: agent role, model, tools, memory type, guardrails
  # Phase 1 recommendation starts with context:
  # "This agent does legal risk assessment with GraphRAG → suggest skill 'legal-risk-patterns'..."
```

### Future verticals (same CLI shape)

```bash
# v2: clean-agents mcp design / validate / render / publish
# v3: clean-agents tool design / validate / render / publish
# v4: clean-agents plugin design / validate / render / publish / convert-from-skill
```

`clean-agents plugin list / run / init` (existing) remains untouched; v4 extends the group non-breakingly.

## Knowledge base strategy

### v1: Flat YAML + embeddings

Extends the existing three-layer knowledge base (`src/clean_agents/knowledge/`) with a new `crafters/` top-level category, subcategorized per vertical:

```
knowledge/
├── architecture-patterns/   # existing
├── frameworks/              # existing
├── models/                  # existing
└── crafters/                # NEW
    ├── skill/
    │   ├── best-practices.yaml    # SKILL.md anatomy, progressive disclosure, trigger design
    │   ├── anti-patterns.yaml     # catalog → feeds L2 validators
    │   ├── templates/             # Jinja2 partials for renderer
    │   └── examples/              # real skills indexed as reference corpus
    ├── mcp/
    ├── tool/
    └── plugin/
```

**Seed sources for v1**:
1. Anthropic official docs (one-time controlled scrape + manual curation)
2. Anti-patterns catalog: 5 entries from the author's own skill review (hardcoded stats, name collision, description length, language mix, missing `version` field) — direct 1:1 mapping to L2/L3 rules
3. Installed skill corpus: scan `~/.claude/plugins/` + `~/.claude/skills/` + project-level (~200 skills available in the author's system). Metadata + frontmatter only, not full body.
4. Marketplace (opt-in, via existing `clean-agents marketplace` command)

**Access layer — interface-first**:

```python
class KnowledgeBase(ABC):
    """Interface — enables future GraphRAG swap without touching consumers."""
    def get_best_practices(self) -> list[BestPractice]: ...
    def get_anti_patterns(self) -> list[AntiPattern]: ...
    def get_similar(self, description: str, k: int = 5) -> list[ArtifactRef]: ...
    def get_template(self, name: str) -> JinjaTemplate: ...

class FlatYAMLKnowledge(KnowledgeBase):
    """v1 implementation — YAML files + MiniLM embeddings (or TF-IDF fallback)."""
```

**Embeddings stack**:
- Primary: `sentence-transformers` MiniLM (~80MB, local, opt-in via `crafters` extra)
- Fallback without ML deps: TF-IDF keyword matching
- **Invariant**: core works offline without ML deps

**KB growth**: reuse existing `clean-agents knowledge add/import/export` commands.

### v2+: GraphRAG migration (deferred)

**Decision**: interface-first in v1 enables drop-in `OntologicalGraphKnowledge` later without touching consumers.

**Migration triggers** (any one activates migration):
- KB corpus exceeds ~500 indexed artifacts
- MCP vertical (v2) implementation begins (MCP resources are natively graph-shaped)
- Meta-agent scope activates

**Candidate stack when triggered**:
- **Kùzu** embedded graph DB (Rust, no server, MIT, Python bindings) — preserves offline invariant
- **Memgraph** if real-time OLAP required
- **LlamaIndex GraphRAG** as abstraction layer

**Rationale for deferral**: artifact relationships (plugin-contains-skill, mcp-exposes-tool, artifact-evolves-from-vN-1) are natively graph-shaped, but premature ontologizing without real corpus risks schema churn. Keep it simple until pain demands complexity.

## Testing strategy

### Invariant

Existing 303 tests must continue to pass. `ruff check src/` clean. `mypy src/` no new errors. ~100 new tests added for crafters.

### Golden fixtures

```
tests/fixtures/crafters/skill/
├── good-skill/                         # passes L1+L2+L3 cleanly
├── bad-hardcoded-stats/                # triggers SKILL-L2-HARDCODED-STATS
├── bad-name-collision/                 # triggers SKILL-L3-NAME-COLLISION
├── bad-language-mix/                   # triggers SKILL-L2-LANGUAGE-MIX
├── bad-desc-too-long/                  # triggers SKILL-L1-DESC-LENGTH
└── leandro-real-skill/                 # regression: author's real skill,
                                        # must produce the 5 findings identified
                                        # in the original skill-reviewer pass
```

The final fixture serves as **regression against a real artifact** — if rule changes stop detecting those 5 findings, the test fails.

### Test categories

- Unit per validator (input fixture → expected findings)
- Unit for renderer (spec → bundle, golden-file comparison)
- Unit for `DesignSession` state machine (phase transitions + save/load round-trip)
- Integration E2E non-interactive: `clean-agents skill design --spec X --no-interactive --output Y`
- AI-mode: Anthropic SDK mocked (no real API calls in CI), VCR fixtures for determinism
- L4 eval harness: LLM responses mocked, TPR/FPR calculation verification

## Error handling

Aligned with existing CLean-agents philosophy (no silent failures, actionable messages):

| Scenario | Handling |
|----------|----------|
| Pydantic validation fail | Rich panel with field path + invalid value + hint |
| Filesystem error (permission, missing) | Retry guidance, never swallow |
| LLM API error in `--ai` mode | Graceful degrade to heuristic + explicit warning ("running without --ai due to: ..."), never silently skip |
| Invalid spec on round-trip | Detailed per-field error with `file:line` pointers |
| L3 Critical collision detected | Blocks render, suggests 3 alternative names |
| L4 thresholds failed | Non-blocking warning, reports concrete failed cases |

## Rollout plan (v1 = Skills vertical)

10 milestones, each a mergeable PR keeping `main` green:

| M | Scope | Depends on |
|---|-------|------------|
| M1 | Base abstractions (`ArtifactSpec`, `DesignSession[T]`, `KnowledgeBase` interface, `ValidatorRegistry`, CLI stubs) | — |
| M2 | **L1** validators complete + fixtures + tests | M1 |
| M3 | **L2** validators complete (including AI-assisted contradictions) | M1, M2 |
| M4 | **L3** validators (filesystem scanner + name/trigger collision; marketplace opt-in) | M1, M2 |
| M5 | `DesignSession` engine + renderer (Jinja2) + `.skill-spec.yaml` round-trip | M1 |
| M6 | CLI wiring: `skill design/validate/render/publish` (interactive + non-interactive) | M5 |
| M7 | AI-enhanced mode integration with existing `ClaudeArchitect` | M5, M6 |
| M8 | **L4** eval harness (opt-in `--eval`) | M6, M7 |
| M9 | Blueprint integration: `AgentSpec.recommended_artifacts`, `--for-agent` flag, `suggest-artifacts` Phase 5 module in `design` | M5, M6 |
| M10 | KB seed (Anthropic docs curation + installed-skills indexer + author's anti-patterns catalog) + docs + release | M1–M9 |

**Execution order**: M1 → (M2, M3, M4 in parallel where bandwidth allows) → M5 → M6 → (M7, M8, M9 in parallel) → M10.

**New optional extra** in `pyproject.toml`:
```toml
[project.optional-dependencies]
crafters = ["sentence-transformers>=2.7"]  # Jinja2 already in core deps
```

## Future directions (parked)

1. **MCP crafter (v2)** — knowledge base from MCP protocol docs; design servers + tools + resources + prompts
2. **Tool crafter (v3)** — cross-framework (OpenAI, Claude, LangChain, MCP)
3. **Plugin crafter (v4)** — aggregator, composes Skills + MCPs + Tools + Agents + Commands + Hooks
4. **GraphRAG migration** — `FlatYAMLKnowledge` → `OntologicalGraphKnowledge` (Kùzu-backed) when any of: corpus >500 artifacts, MCP vertical in scope, meta-agent activated. Interface abstracts access in v1 to enable drop-in swap.
5. **L5 skill-shield** — adversarial module parallel to existing CLean-shield (prompt injection via description, cross-skill poisoning, system prompt extraction via activation)
6. **Meta-agent** — autonomous CLean-agents operator that consumes/produces specs without human in the loop. All v1 design choices (structured IO, SDK-first, typed errors, idempotent ops) intentionally support this direction.
7. **Multi-language output** — design of artifacts in languages beyond en/es/pt
8. **Refactor existing `design`** — reuse `DesignSession[T]` to unify Blueprint + crafter flows

## Open questions

None. All scope decisions closed during 2026-04-21 brainstorming session.

## Intentional tech debt

- **`clean-agents design` (Blueprint flow) not refactored in v1** to share the new `DesignSession[T]` engine. Refactor is viable (engine designed for reuse) but explicitly deferred.
- **Flat YAML KB in v1** instead of GraphRAG. Interface-based access layer enables future migration; see Future Directions #4 for triggers.
- **L4 eval harness uses simulated skill activation** (system-prompt injection) rather than real Claude Code skill loading. Real-loading fidelity requires deeper Claude Code integration, deferred.
