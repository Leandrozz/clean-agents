# Crafters — Reference

Deep-dive for the `crafters/` vertical shipped in CLean-agents 0.2.0. Covers the Skills designer (v1); MCP / Tool / Plugin verticals will follow the same shape.

The headline: crafters turns natural-language artifact descriptions into validated, renderable bundles. The hard part in building a Claude Code skill isn't writing markdown — it's writing markdown that **activates for the right prompts, doesn't collide with other skills, and doesn't age poorly**. Crafters encodes that expertise as 15 validator rules.

---

## The `.skill-spec.yaml` schema

Every skill has one source of truth: a `.skill-spec.yaml` at the bundle root. This is what `skill validate` reads and `skill render` consumes.

```yaml
name: legal-risk-review                          # kebab-case, matches the bundle dir name
version: 0.1.0
description: >                                    # 50..500 chars — short enough to stay scannable
  Reviews legal contracts and NDAs for risk clauses typical of enterprise
  procurement. Built for the risk_evaluator agent in our procurement blueprint.
artifact_type: skill
language: en                                      # ISO 639-1; mixing languages in body triggers L2
license: MIT
author: Leandro
triggers:                                         # 3-7 activation keywords, lowercase, single tokens
  - nda
  - risk clause
  - liability cap
references:                                       # progressive disclosure — move detail here
  - path: references/clauses.md
    topic: Catalogue of risky clauses with examples
    outline: ["Liability", "Indemnification", "IP assignment"]
    mentioned_in: ["overview", "how-to"]         # anchors in SKILL.md that link here
body_outline:                                     # structured sections that render into SKILL.md
  - heading: Overview
    anchor: overview
    body: >
      When this skill activates, you're reviewing a legal document for the
      risk patterns catalogued in references/clauses.md...
  - heading: How to use
    anchor: how-to
    body: >
      Walk through the document section by section. For each clause...
evals:                                            # optional L4 runtime config
  positive_cases:
    - prompt: "Review this NDA for unusual liability clauses"
      expected: activate
  negative_cases:
    - prompt: "What's the weather today?"
      expected: ignore
  thresholds:
    tpr_min: 0.8
    fpr_max: 0.2
bundle_format: dir                                # 'dir' (default) or 'zip' when publishing
```

The full Pydantic model lives at `clean_agents.crafters.skill.spec.SkillSpec`.

---

## Validator catalogue (15 rules)

Each rule has an ID of the form `SKILL-L<level>-<slug>`. Levels: L1 (structural), L2 (content), L3 (ecosystem), L4 (runtime). Severities: INFO / MEDIUM / HIGH / CRITICAL.

### L1 — Structural (always runs)

| Rule ID | Severity | What it checks |
|---|---|---|
| `SKILL-L1-NAME-DIR` | HIGH | `spec.name` matches the bundle directory basename (case-sensitive). Enforces filesystem discoverability. |
| `SKILL-L1-DESC-LENGTH` | MEDIUM | `len(description)` is in `[50, 500]`. Shorter = uninformative; longer = doesn't fit activation previews. |
| `SKILL-L1-REQUIRED-SECTIONS` | HIGH | `body_outline` contains the minimum required sections (currently "Overview"). |
| `SKILL-L1-REFERENCES-EXIST` | HIGH | Every `references[i].path` resolves to a real file inside the bundle. Prevents silent 404s when Claude follows a link. |
| `SKILL-L1-TRIGGER-SHAPE` | MEDIUM | Triggers are lowercase, 1-3 tokens each, no punctuation. Keeps activation predictable. |

### L2 — Content quality

| Rule ID | Severity | What it checks |
|---|---|---|
| `SKILL-L2-HARDCODED-STATS` | MEDIUM | Body text contains `\d+\.\d+\s?%`, `CVE-YYYY-N`, or `paper de YYYY` — stats that age poorly. Move to `references/` or rephrase relatively. |
| `SKILL-L2-HARDCODED-DATES` | LOW | Body text contains bare year tokens (`2024`, `2025`) that will look stale within a year. |
| `SKILL-L2-LANGUAGE-MIX` | MEDIUM | A body section is in a language different from `spec.language` (simple EN/ES hint-word vote). Pick one and stick to it. |
| `SKILL-L2-TRIGGER-COVERAGE` | MEDIUM | Each trigger appears at least once in the body or references. Otherwise the trigger is a vibe, not a contract. |
| `SKILL-L2-PROGRESSIVE-DISCLOSURE` | LOW | SKILL.md body stays under ~1500 chars per section; anything longer should go to `references/`. |
| `SKILL-L2-PROMISES-VS-DELIVERY` | MEDIUM | Every capability the description promises has a corresponding section in `body_outline`. No overselling. |
| `SKILL-L2-CONTRADICTIONS` | HIGH (AI) | With `--ai`, uses Claude to detect logical contradictions across sections (e.g. "always validate" + "skip validation when X"). Silent without `--ai`. |

### L3 — Ecosystem

| Rule ID | Severity | What it checks |
|---|---|---|
| `SKILL-L3-NAME-COLLISION` | CRITICAL | `spec.name` doesn't collide with a skill already installed under `~/.claude/skills/` or `~/.claude/plugins/*/skills/`. A collision silently shadows one of the two. |
| `SKILL-L3-MARKETPLACE-DEDUPE` | HIGH | `spec.name` isn't already published to the configured marketplace (if any). |
| `SKILL-L3-TRIGGER-OVERLAP` | MEDIUM | Jaccard similarity of trigger sets against installed skills stays below 0.5. High overlap = confused activation. |

### L4 — Runtime (opt-in with `--eval`, requires `ANTHROPIC_API_KEY`)

| Rule ID | Severity | What it checks |
|---|---|---|
| `SKILL-L4-ACTIVATION-PRECISION` | HIGH | Runs `spec.evals.{positive,negative}_cases` through a Haiku-backed activation harness. Fails if TPR < `tpr_min` or FPR > `fpr_max`. |

---

## The iteration loop

Crafters is designed for Claude-in-the-loop iteration, not one-shot generation.

```
clean-agents skill design "..."        →  produces draft .skill-spec.yaml
clean-agents skill validate ./bundle   →  lists findings
    fix SKILL.md / spec YAML per fix_hint on each finding
clean-agents skill validate ./bundle   →  re-check
    when clean, optionally:
clean-agents skill validate ./bundle --ai --eval
    ↑ adds L2-CONTRADICTIONS (Claude) and L4-ACTIVATION-PRECISION (Haiku harness)
clean-agents skill render ./bundle --output ./dist --zip
```

Every finding carries a `fix_hint` that tells the engineer exactly what to change. When Claude Code dispatches to the CLI, it should read the JSON format (`--format json`) and loop: invoke, parse findings, propose the fix, re-validate.

---

## Common findings and how to fix them

**SKILL-L2-HARDCODED-STATS fires on `82.4%`**
→ Rephrase to a relative claim ("majority", "most benchmarks show improvement") or move the exact stat into `references/` with a note on when it was measured.

**SKILL-L2-LANGUAGE-MIX fires when `spec.language: en` but a body section is in Spanish**
→ Either translate the section or change `spec.language`. Don't mix in the same skill — pick the dominant language and keep it consistent.

**SKILL-L3-NAME-COLLISION fires on `my-skill`**
→ The user has another skill with that name installed. Either rename (e.g. `my-skill-legal`) or uninstall the colliding skill. Run `clean-agents skill list --installed` to see what's colliding.

**SKILL-L4-ACTIVATION-PRECISION fires with TPR=0.6**
→ Triggers are too narrow. Add more positive eval cases, or broaden the `triggers:` list, or add synonyms to the body. Re-run `--eval` until TPR crosses the threshold.

---

## Bidirectional blueprint link

Starting in 0.2.0, `AgentSpec` has a `recommended_artifacts: list[ArtifactRef]` field. An `ArtifactRef` points to a crafter-designed artifact and carries a rationale:

```yaml
# blueprint.yaml fragment
agents:
  - name: risk_evaluator
    role: legal risk assessor
    recommended_artifacts:
      - artifact_type: skill
        name: legal-risk-review
        rationale: agent works with legal jargon
        spec_path: .clean-agents/skills/legal-risk-review/.skill-spec.yaml
        status: needed                  # needed | designed | rendered | published
```

Two CLI entry points power this loop:

- `skill design --for-agent <name> --blueprint blueprint.yaml` pre-loads agent context (role, model, memory shape) into the skill design prompt so the generated draft is agent-aware.
- `design --blueprint blueprint.yaml --module suggest-artifacts` scans every agent's role and proposes candidate artifacts with rationales. Output is a table of `--for-agent` commands the engineer can run next.

---

## Architecture pointers (for the curious)

- **Entry-point registry** — the 15 validators are declared in `pyproject.toml` under `[project.entry-points."clean_agents.validators"]`. Third-party packages can register their own rules by shipping an entry point in the same group.
- **Knowledge base** — seed best-practices and anti-patterns live at `knowledge/crafters/skill/*.yaml`. `SkillKnowledge` loads them lazily and exposes `get_best_practices`, `get_anti_patterns`, `get_similar` (scans installed skills for keyword overlap).
- **Templates** — `render` uses Jinja2 templates at `src/clean_agents/crafters/skill/templates/` to emit `SKILL.md`, `README.md`, and the evals JSON.
- **AI integration** — `--ai` routes through `clean_agents.integrations.anthropic.get_architect()`. Missing `ANTHROPIC_API_KEY` degrades gracefully to heuristics with a yellow warning.

For implementation details, see `src/clean_agents/crafters/` in the repo. For the spec and plan of record, see `docs/superpowers/specs/2026-04-21-crafters-module-design.md` and `docs/superpowers/plans/2026-04-21-crafters-module.md`.
