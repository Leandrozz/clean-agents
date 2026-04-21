"""Anthropic Claude integration for AI-enhanced architecture design.

Uses Claude to enrich recommendations with deeper analysis, custom agent
prompt generation, and interactive design iteration.
"""

from __future__ import annotations

import json
import json as _json_ca
from typing import Any

from clean_agents.core.blueprint import Blueprint


class _SkillCrafterMixin:
    """Mixin pulled into ClaudeArchitect for skill-crafter-specific calls."""

    def detect_contradictions(self, text: str) -> list[str]:
        prompt = (
            "You are reviewing a Claude Code skill body for internal contradictions. "
            "Reply with a JSON array of short sentences describing contradictions. "
            "Return [] if there are none.\n\n"
            f"--- BEGIN BODY ---\n{text}\n--- END BODY ---"
        )
        resp = self._client.messages.create(
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
        resp = self._client.messages.create(
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
        resp = self._client.messages.create(
            model="claude-haiku-4-5", max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return _json_ca.loads(resp.content[0].text)
        except Exception:
            return {"positive": [], "negative": []}


class ClaudeArchitect(_SkillCrafterMixin):
    """AI-powered architecture consultant using Claude.

    Wraps the Anthropic SDK to provide high-level methods for
    architecture design, security analysis, and prompt generation.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        client: Any | None = None,
    ) -> None:
        if client is not None:
            self._client = client
        else:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install clean-agents"
                )
            self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def enhance_blueprint(self, blueprint: Blueprint) -> dict[str, Any]:
        """Use Claude to analyze and suggest improvements to a blueprint.

        Returns a dict with:
          - suggestions: list of improvement suggestions
          - risk_assessment: overall risk analysis
          - missing_components: things the blueprint should address
        """
        prompt = f"""You are CLean-agents, an expert agentic systems architect.

Analyze this architecture blueprint and provide:
1. Top 3-5 improvement suggestions with specific, actionable changes
2. Risk assessment (security, reliability, cost)
3. Missing components or considerations

Blueprint YAML:
```yaml
{blueprint.to_yaml()}
```

Respond in JSON format:
{{
  "suggestions": [
    {{"title": "...", "description": "...", "priority": "high|medium|low", "impact": "..."}}
  ],
  "risk_assessment": {{
    "security": {{"level": "low|medium|high", "details": "..."}},
    "reliability": {{"level": "low|medium|high", "details": "..."}},
    "cost": {{"level": "low|medium|high", "details": "..."}}
  }},
  "missing_components": ["..."]
}}"""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        # Extract JSON from response
        try:
            # Try direct parse first
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting from markdown code block
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            return {"raw_response": text, "suggestions": [], "risk_assessment": {}, "missing_components": []}

    def generate_agent_prompt(
        self,
        agent_name: str,
        agent_role: str,
        domain: str,
        constraints: list[str] | None = None,
        tools: list[str] | None = None,
    ) -> str:
        """Generate an optimized system prompt for a specific agent."""
        constraints_str = "\n".join(f"- {c}" for c in (constraints or []))
        tools_str = "\n".join(f"- {t}" for t in (tools or []))

        prompt = f"""You are a prompt engineering expert. Generate an optimized system prompt for an AI agent.

Agent name: {agent_name}
Role: {agent_role}
Domain: {domain}
Constraints:
{constraints_str or '- None specified'}
Available tools:
{tools_str or '- None specified'}

Generate a production-quality system prompt that:
1. Clearly defines the agent's identity and boundaries
2. Includes specific instructions for the domain
3. Has safety guardrails built-in
4. Uses structured output formatting
5. Handles edge cases gracefully

Output ONLY the system prompt text, no explanations."""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def analyze_security(self, blueprint: Blueprint) -> dict[str, Any]:
        """Deep security analysis using Claude's reasoning."""
        prompt = f"""You are CLean-shield, a security expert for agentic AI systems.

Perform a thorough security analysis of this architecture:

```yaml
{blueprint.to_yaml()}
```

For each agent, analyze:
1. Prompt injection attack surface
2. Data leakage risk
3. Tool abuse potential
4. Privilege escalation paths
5. Inter-agent trust boundaries

Respond in JSON:
{{
  "overall_score": 0-100,
  "critical_findings": [{{"agent": "...", "vulnerability": "...", "severity": "critical|high|medium|low", "remediation": "..."}}],
  "attack_scenarios": [{{"name": "...", "steps": ["..."], "impact": "...", "mitigation": "..."}}],
  "hardening_checklist": ["..."]
}}"""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            return {"raw_response": text, "overall_score": 0, "critical_findings": []}

    def iterate_design(
        self,
        blueprint: Blueprint,
        user_feedback: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Interactive design iteration — user provides feedback, Claude adjusts.

        Returns YAML diff or updated blueprint section.
        """
        messages = list(conversation_history or [])

        messages.append({
            "role": "user",
            "content": f"""Current blueprint:
```yaml
{blueprint.to_yaml()}
```

User feedback: {user_feedback}

Suggest specific changes to the blueprint based on this feedback.
Format your response as:
1. What to change and why
2. Updated YAML sections (only the changed parts)
3. Impact on cost, security, and reliability""",
        })

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system="You are CLean-agents, an expert agentic systems architect. Help the user iterate on their architecture design. Be specific, evidence-backed, and concise.",
            messages=messages,
        )
        return response.content[0].text
