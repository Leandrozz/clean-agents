"""FastAPI server for CLean-agents — REST API for architecture design.

Endpoints:
    POST /api/design          → Generate a blueprint from description
    GET  /api/blueprint       → Get the current blueprint
    POST /api/blueprint/iter  → Iterate on the design with feedback
    POST /api/shield          → Run security analysis
    POST /api/cost            → Run cost simulation
    POST /api/scaffold        → Generate starter code
    GET  /api/health          → Health check

Authentication:
    - API key in X-API-Key header or Authorization: Bearer <key> header
    - Rate limiting: Requests per minute per key (configurable)
    - Backward compatible: disabled by default
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config
from clean_agents.engine.recommender import Recommender
from clean_agents.server.auth import AuthManager, AuthConfig

logger = logging.getLogger(__name__)

# Blueprint store (in-memory for single-user mode)
_current_blueprint: Blueprint | None = None
_auth_manager: AuthManager | None = None


def create_app(auth_config: Optional[AuthConfig] = None):
    """Create and configure the FastAPI application.

    Args:
        auth_config: Optional AuthConfig for authentication/rate limiting
    """
    try:
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
    except ImportError:
        raise ImportError(
            "FastAPI required for server mode. Install with: pip install clean-agents[api]"
        )

    global _auth_manager
    _auth_manager = AuthManager(auth_config)

    app = FastAPI(
        title="CLean-agents API",
        description="Design, plan, and harden production-grade agentic AI systems",
        version="0.1.0",
    )

    # ── CORS Middleware ──────────────────────────────────────────────────────

    cors_origins = [
        origin.strip()
        for origin in (os.getenv("CLEAN_AGENTS_CORS_ORIGINS", "*")).split(",")
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Authentication & Logging Middleware ─────────────────────────────────

    @app.middleware("http")
    async def auth_and_logging_middleware(request: Request, call_next):
        """Middleware for authentication and request logging.

        Auth checks happen here before body parsing to return 401/429
        before any unprocessable entity errors.
        """
        # Skip auth for health endpoint
        if request.url.path != "/api/health":
            # Extract key from headers
            api_key = request.headers.get("X-API-Key") or None
            if not api_key:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    api_key = auth_header[7:].strip()

            # Validate if auth is enabled
            if _auth_manager.config.enabled:
                if not _auth_manager.validate_key(api_key):
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid or missing API key. Provide via X-API-Key header or Authorization: Bearer <key>"},
                    )

                # Check rate limit
                if not _auth_manager.check_rate_limit(api_key):
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=429,
                        content={"detail": f"Rate limit exceeded. Max {_auth_manager.config.rate_limit_rpm} requests per minute."},
                    )

        # Log and process request
        start_time = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} {latency_ms:.1f}ms"
        )
        return response

    # ── Request/Response models ──────────────────────────────────────────

    class DesignRequest(BaseModel):
        description: str
        language: str = "en"

    class IterateRequest(BaseModel):
        feedback: str

    class CostRequest(BaseModel):
        monthly_requests: int = 10000

    class ScaffoldRequest(BaseModel):
        framework: str = ""
        output_dir: str = "./generated"

    # ── Endpoints ────────────────────────────────────────────────────────

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint (no auth required)."""
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/api/design")
    def design(request: DesignRequest) -> dict[str, Any]:
        """Generate a new architecture blueprint."""
        global _current_blueprint

        recommender = Recommender()
        blueprint = recommender.recommend(request.description, language=request.language)
        _current_blueprint = blueprint

        # Auto-save
        config = Config.discover()
        try:
            blueprint.save(config.blueprint_path())
        except Exception:
            pass  # Non-critical — might not have a project dir

        return {
            "blueprint": blueprint.model_dump(mode="json", exclude_none=True),
            "summary": blueprint.summary(),
        }

    @app.get("/api/blueprint")
    def get_blueprint() -> dict[str, Any]:
        """Get the current blueprint."""
        bp = _load_or_current()
        return {
            "blueprint": bp.model_dump(mode="json", exclude_none=True),
            "summary": bp.summary(),
        }

    @app.post("/api/blueprint/iter")
    def iterate(request: IterateRequest) -> dict[str, Any]:
        """Iterate on the design with user feedback."""
        bp = _load_or_current()

        # For now, return the feedback as a changelog entry
        # AI-enhanced iteration requires anthropic integration
        bp.changelog.append(f"Feedback: {request.feedback}")
        bp.iteration += 1

        global _current_blueprint
        _current_blueprint = bp

        return {
            "blueprint": bp.model_dump(mode="json", exclude_none=True),
            "summary": bp.summary(),
            "iteration": bp.iteration,
            "note": "AI-enhanced iteration available with ANTHROPIC_API_KEY configured",
        }

    @app.post("/api/shield")
    def shield() -> dict[str, Any]:
        """Run security analysis."""
        bp = _load_or_current()

        from clean_agents.cli.shield_cmd import ATTACK_CATEGORIES, _analyze_category

        results = {}
        total_fails = 0
        total_warns = 0
        total_checks = 0

        for cat in ATTACK_CATEGORIES:
            findings = _analyze_category(bp, cat)
            fails = [f for f in findings if f["status"] == "FAIL"]
            warns = [f for f in findings if f["status"] == "WARN"]
            total_fails += len(fails)
            total_warns += len(warns)
            total_checks += len(findings)

            results[cat["id"]] = {
                "name": cat["name"],
                "description": cat["description"],
                "findings": findings,
                "fails": len(fails),
                "warns": len(warns),
            }

        return {
            "categories": results,
            "total_checks": total_checks,
            "total_fails": total_fails,
            "total_warns": total_warns,
            "score": round((total_checks - total_fails) / total_checks * 100, 1) if total_checks else 100,
        }

    @app.post("/api/cost")
    def cost(request: CostRequest) -> dict[str, Any]:
        """Run cost simulation."""
        bp = _load_or_current()

        pricing = {
            "claude-opus-4-6": (5.0, 25.0),
            "claude-sonnet-4-6": (3.0, 15.0),
            "claude-haiku-4-5": (1.0, 5.0),
            "gpt-4o": (2.5, 10.0),
            "gpt-4o-mini": (0.15, 0.60),
            "gemini-2.5-pro": (4.0, 20.0),
            "gemini-2.5-flash": (0.30, 2.50),
        }

        agents_cost = []
        total_per_request = 0.0

        for agent in bp.agents:
            ip, op = pricing.get(agent.model.primary, (3.0, 15.0))
            input_tokens = agent.total_input_tokens_estimate()
            output_tokens = agent.token_budget
            cost = (input_tokens / 1_000_000 * ip) + (output_tokens / 1_000_000 * op)
            total_per_request += cost
            agents_cost.append({
                "agent": agent.name,
                "model": agent.model.primary,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_per_call": round(cost, 6),
            })

        monthly_llm = total_per_request * request.monthly_requests
        infra = 0.0
        if bp.infrastructure.vector_db:
            infra += 50.0
        if bp.infrastructure.graph_db:
            infra += 100.0
        if bp.infrastructure.message_queue:
            infra += 20.0
        if bp.infrastructure.observability:
            infra += 30.0

        return {
            "per_request": round(total_per_request, 6),
            "monthly_llm": round(monthly_llm, 2),
            "monthly_infra": round(infra, 2),
            "monthly_total": round(monthly_llm + infra, 2),
            "monthly_requests": request.monthly_requests,
            "agents": agents_cost,
        }

    @app.post("/api/scaffold")
    def scaffold(request: ScaffoldRequest) -> dict[str, Any]:
        """Generate scaffold info (does not write files via API)."""
        bp = _load_or_current()
        framework = request.framework or bp.framework

        return {
            "framework": framework,
            "agents": [
                {
                    "name": a.name,
                    "type": a.agent_type,
                    "model": a.model.primary,
                    "role": a.role,
                }
                for a in bp.agents
            ],
            "note": f"Use CLI `clean-agents scaffold -o {request.output_dir}` to generate files",
        }

    def _load_or_current() -> Blueprint:
        """Load blueprint from disk or use in-memory."""
        global _current_blueprint
        if _current_blueprint:
            return _current_blueprint

        config = Config.discover()
        bp_path = config.blueprint_path()
        if bp_path.exists():
            _current_blueprint = Blueprint.load(bp_path)
            return _current_blueprint

        raise HTTPException(
            status_code=404,
            detail="No blueprint found. POST /api/design first.",
        )

    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    auth_config: Optional[AuthConfig] = None,
) -> None:
    """Run the API server.

    Args:
        host: Bind host
        port: Bind port
        auth_config: Optional AuthConfig for authentication/rate limiting
    """
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn required for server mode. Install with: pip install clean-agents[api]"
        )

    app = create_app(auth_config)
    uvicorn.run(app, host=host, port=port)
