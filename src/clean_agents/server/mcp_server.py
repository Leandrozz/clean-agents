"""MCP (Model Context Protocol) server for IDE integration.

Exposes CLean-agents capabilities as MCP tools that can be used
from Claude Code, VS Code, Cursor, or any MCP-compatible client.

Tools exposed:
    clean_agents_design     → Generate architecture from description
    clean_agents_blueprint  → Get current blueprint as YAML
    clean_agents_shield     → Run security analysis
    clean_agents_cost       → Run cost simulation
    clean_agents_models     → Get model recommendations
"""

from __future__ import annotations

import json
from typing import Any

MCP_MANIFEST = {
    "name": "clean-agents",
    "version": "0.1.0",
    "description": "Agentic architecture design, security hardening, and cost analysis",
    "tools": [
        {
            "name": "clean_agents_design",
            "description": "Design an agentic AI system architecture from a natural language description. Returns a complete blueprint with agent specs, infrastructure, compliance mapping, and cost estimates.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the system to build",
                    },
                    "language": {
                        "type": "string",
                        "description": "Output language (en, es, pt, fr, de)",
                        "default": "en",
                    },
                },
                "required": ["description"],
            },
        },
        {
            "name": "clean_agents_blueprint",
            "description": "Get the current architecture blueprint as YAML",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "clean_agents_shield",
            "description": "Run security hardening analysis on the current blueprint. Checks 7 attack categories: prompt injection, jailbreaking, data extraction, agent manipulation, tool abuse, DoS, privacy violation.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Specific attack category (ATK-1 to ATK-7) or 'all'",
                        "default": "all",
                    },
                },
            },
        },
        {
            "name": "clean_agents_cost",
            "description": "Run cost simulation for the current blueprint",
            "input_schema": {
                "type": "object",
                "properties": {
                    "monthly_requests": {
                        "type": "integer",
                        "description": "Expected monthly request volume",
                        "default": 10000,
                    },
                },
            },
        },
        {
            "name": "clean_agents_models",
            "description": "Get model recommendations for each agent in the current blueprint, based on benchmarks (GPQA, SWE-Bench, BFCL) and cost optimization.",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
    ],
}


class MCPServer:
    """MCP server that wraps CLean-agents tools.

    This is a simplified implementation. For production use,
    integrate with the official MCP SDK.
    """

    def __init__(self) -> None:
        from clean_agents.core.blueprint import Blueprint
        from clean_agents.core.config import Config
        from clean_agents.engine.recommender import Recommender

        self._recommender = Recommender()
        self._config = Config.discover()
        self._blueprint: Blueprint | None = None

    def get_manifest(self) -> dict[str, Any]:
        """Return the MCP tool manifest."""
        return MCP_MANIFEST

    def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a tool call to the appropriate handler."""
        handlers = {
            "clean_agents_design": self._handle_design,
            "clean_agents_blueprint": self._handle_blueprint,
            "clean_agents_shield": self._handle_shield,
            "clean_agents_cost": self._handle_cost,
            "clean_agents_models": self._handle_models,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return handler(arguments)
        except Exception as e:
            return {"error": str(e)}

    def _handle_design(self, args: dict[str, Any]) -> dict[str, Any]:
        description = args.get("description", "")
        language = args.get("language", "en")

        if not description:
            return {"error": "description is required"}

        blueprint = self._recommender.recommend(description, language=language)
        self._blueprint = blueprint

        # Save to project
        try:
            blueprint.save(self._config.blueprint_path())
        except Exception:
            pass

        return {
            "blueprint_yaml": blueprint.to_yaml(),
            "summary": blueprint.summary(),
        }

    def _handle_blueprint(self, args: dict[str, Any]) -> dict[str, Any]:
        bp = self._get_blueprint()
        if not bp:
            return {"error": "No blueprint found. Run clean_agents_design first."}

        return {
            "yaml": bp.to_yaml(),
            "summary": bp.summary(),
        }

    def _handle_shield(self, args: dict[str, Any]) -> dict[str, Any]:
        bp = self._get_blueprint()
        if not bp:
            return {"error": "No blueprint found. Run clean_agents_design first."}

        from clean_agents.cli.shield_cmd import ATTACK_CATEGORIES, _analyze_category

        category_filter = args.get("category", "all")

        results = {}
        total_fails = 0

        for cat in ATTACK_CATEGORIES:
            if category_filter != "all" and cat["id"].lower() != category_filter.lower():
                continue

            findings = _analyze_category(bp, cat)
            fails = [f for f in findings if f["status"] == "FAIL"]
            warns = [f for f in findings if f["status"] == "WARN"]
            total_fails += len(fails)

            results[cat["id"]] = {
                "name": cat["name"],
                "fails": len(fails),
                "warns": len(warns),
                "critical_findings": [f for f in findings if f["status"] in ("FAIL", "WARN")],
            }

        return {"results": results, "total_issues": total_fails}

    def _handle_cost(self, args: dict[str, Any]) -> dict[str, Any]:
        bp = self._get_blueprint()
        if not bp:
            return {"error": "No blueprint found. Run clean_agents_design first."}

        monthly_requests = args.get("monthly_requests", 10000)
        per_request = bp.estimated_cost_per_request()
        monthly = per_request * monthly_requests

        return {
            "per_request": f"${per_request:.5f}",
            "monthly_llm": f"${monthly:,.2f}",
            "monthly_requests": monthly_requests,
            "agents": [
                {"name": a.name, "model": a.model.primary, "tokens": a.token_budget}
                for a in bp.agents
            ],
        }

    def _handle_models(self, args: dict[str, Any]) -> dict[str, Any]:
        bp = self._get_blueprint()
        if not bp:
            return {"error": "No blueprint found. Run clean_agents_design first."}

        from clean_agents.cli.module_cmds import _recommend_model

        benchmarks = {
            "claude-opus-4-6": {"GPQA": 72.5, "SWE-Bench": 72.0, "BFCL": 88.0},
            "claude-sonnet-4-6": {"GPQA": 65.0, "SWE-Bench": 65.0, "BFCL": 90.5},
            "claude-haiku-4-5": {"GPQA": 41.0, "SWE-Bench": 41.0, "BFCL": 80.2},
            "gpt-4o": {"GPQA": 53.6, "SWE-Bench": 33.2, "BFCL": 87.0},
        }

        recommendations = []
        for agent in bp.agents:
            rec, rationale = _recommend_model(agent, benchmarks)
            recommendations.append({
                "agent": agent.name,
                "current": agent.model.primary,
                "recommended": rec,
                "rationale": rationale,
                "change_needed": rec != agent.model.primary,
            })

        return {"recommendations": recommendations}

    def _get_blueprint(self):
        """Get blueprint from memory or disk."""
        if self._blueprint:
            return self._blueprint

        from clean_agents.core.blueprint import Blueprint

        bp_path = self._config.blueprint_path()
        if bp_path.exists():
            self._blueprint = Blueprint.load(bp_path)
            return self._blueprint

        return None


def run_mcp_stdio() -> None:
    """Run MCP server in stdio mode (for IDE integration).

    Reads JSON-RPC messages from stdin, processes them, writes to stdout.
    This is a minimal implementation — for production, use the MCP SDK.
    """
    import sys

    server = MCPServer()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method", "")
        req_id = request.get("id")

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "clean-agents", "version": "0.1.0"},
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": MCP_MANIFEST["tools"]},
            }
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = server.handle_tool_call(tool_name, arguments)
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                },
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
