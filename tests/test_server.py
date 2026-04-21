"""Tests for the MCP server tool handler."""

from clean_agents.server.mcp_server import MCPServer, MCP_MANIFEST


def test_mcp_manifest_tools():
    tools = MCP_MANIFEST["tools"]
    assert len(tools) >= 5
    names = [t["name"] for t in tools]
    assert "clean_agents_design" in names
    assert "clean_agents_shield" in names
    assert "clean_agents_cost" in names


def test_mcp_server_design():
    server = MCPServer()
    result = server.handle_tool_call("clean_agents_design", {
        "description": "Simple FAQ chatbot for customer support",
    })
    assert "blueprint_yaml" in result or "summary" in result
    assert "error" not in result


def test_mcp_server_blueprint_after_design():
    server = MCPServer()
    # Design first
    server.handle_tool_call("clean_agents_design", {
        "description": "Legal contract review system with GDPR compliance",
    })
    # Then get blueprint
    result = server.handle_tool_call("clean_agents_blueprint", {})
    assert "yaml" in result
    assert "error" not in result


def test_mcp_server_shield():
    server = MCPServer()
    server.handle_tool_call("clean_agents_design", {
        "description": "Medical diagnosis assistant handling patient records",
    })
    result = server.handle_tool_call("clean_agents_shield", {"category": "all"})
    assert "results" in result
    assert "error" not in result


def test_mcp_server_cost():
    server = MCPServer()
    server.handle_tool_call("clean_agents_design", {
        "description": "E-commerce recommendation engine",
    })
    result = server.handle_tool_call("clean_agents_cost", {"monthly_requests": 5000})
    assert "per_request" in result
    assert "error" not in result


def test_mcp_server_no_blueprint():
    import os
    # Ensure we're not in a directory with a .clean-agents project
    old_cwd = os.getcwd()
    os.chdir("/")
    try:
        server = MCPServer()
        server._blueprint = None  # Force no in-memory blueprint
        server._config.project_dir = "/nonexistent/.clean-agents"
        result = server.handle_tool_call("clean_agents_blueprint", {})
        assert "error" in result
    finally:
        os.chdir(old_cwd)


def test_mcp_server_unknown_tool():
    server = MCPServer()
    result = server.handle_tool_call("nonexistent_tool", {})
    assert "error" in result
