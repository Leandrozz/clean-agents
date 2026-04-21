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
