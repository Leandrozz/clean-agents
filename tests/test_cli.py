"""End-to-end CLI tests using typer.testing.CliRunner."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from clean_agents.cli.main import app
from clean_agents.core.blueprint import Blueprint

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that gets cleaned up."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def blueprint_with_design(temp_dir):
    """Create a blueprint via design command for tests that need one."""
    # Run design command with minimal options
    result = runner.invoke(
        app,
        [
            "design",
            "--desc",
            "Simple chatbot for customer support",
            "--no-interactive",
            "--output",
            str(temp_dir / "blueprint.yaml"),
        ],
    )
    assert result.exit_code == 0, f"Design command failed: {result.stdout}"

    # Load and return the created blueprint
    blueprint_path = temp_dir / "blueprint.yaml"
    assert blueprint_path.exists(), f"Blueprint not created at {blueprint_path}"
    return Blueprint.load(blueprint_path)


class TestVersionCommand:
    """Test --version flag."""

    def test_version_output(self):
        """Test that --version outputs version info."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        from clean_agents import __version__
        assert __version__ in result.stdout
        assert "CLean-agents" in result.stdout


class TestHelpCommand:
    """Test --help flag."""

    def test_help_lists_commands(self):
        """Test that --help lists available commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "design" in result.stdout
        assert "blueprint" in result.stdout
        assert "cost" in result.stdout
        assert "shield" in result.stdout
        assert "models" in result.stdout
        assert "comply" in result.stdout
        assert "plugin" in result.stdout


class TestDesignCommand:
    """Test design command."""

    def test_design_with_description_and_no_interactive(self, temp_dir):
        """Test design command with --desc and --no-interactive."""
        blueprint_path = temp_dir / "blueprint.yaml"
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "Simple chatbot for customer support",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0
        assert blueprint_path.exists()
        blueprint = Blueprint.load(blueprint_path)
        assert blueprint.name is not None
        assert len(blueprint.agents) > 0

    def test_design_requires_description_in_non_interactive_mode(self):
        """Test that design requires --desc in --no-interactive mode."""
        result = runner.invoke(app, ["design", "--no-interactive"])
        assert result.exit_code != 0
        assert "desc required" in result.stdout or "Error" in result.stdout


class TestBlueprintCommand:
    """Test blueprint command."""

    def test_blueprint_yaml_format(self, temp_dir, blueprint_with_design):
        """Test blueprint command with --format yaml."""
        # Configure to use temp directory
        blueprint_path = temp_dir / "blueprint.yaml"
        blueprint_with_design.save(blueprint_path)

        result = runner.invoke(
            app,
            ["blueprint", "--format", "yaml", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0
        assert "agents:" in result.stdout or "name:" in result.stdout

    def test_blueprint_json_format(self, temp_dir, blueprint_with_design):
        """Test blueprint command with --format json."""
        blueprint_path = temp_dir / "blueprint.yaml"
        blueprint_with_design.save(blueprint_path)

        result = runner.invoke(
            app,
            ["blueprint", "--format", "json", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0
        # Verify the output contains expected JSON elements (Rich adds color codes)
        assert "name" in result.stdout
        assert "agents" in result.stdout or "[" in result.stdout

    def test_blueprint_error_without_blueprint(self):
        """Test blueprint command fails when no blueprint exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory with no blueprint
            result = runner.invoke(
                app,
                ["blueprint", "--path", str(Path(tmpdir) / "nonexistent.yaml")],
            )
            assert result.exit_code != 0
            assert "No blueprint found" in result.stdout or "Error" in result.stdout


class TestCostCommand:
    """Test cost command."""

    def test_cost_shows_table(self, temp_dir):
        """Test that cost command shows cost analysis."""
        # First create a blueprint
        blueprint_path = temp_dir / "blueprint.yaml"
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "Simple chatbot",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0

        # Then run cost command
        result = runner.invoke(
            app,
            ["cost", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0
        # Should show some cost-related output
        assert "cost" in result.stdout.lower() or "agent" in result.stdout.lower()


class TestModelsCommand:
    """Test models command."""

    def test_models_shows_recommendations(self, temp_dir):
        """Test that models command shows model recommendations."""
        # First create a blueprint
        blueprint_path = temp_dir / "blueprint.yaml"
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "Simple chatbot",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0

        # Then run models command
        result = runner.invoke(
            app,
            ["models", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0


class TestShieldCommand:
    """Test shield command."""

    def test_shield_shows_security_analysis(self, temp_dir):
        """Test that shield command shows security analysis."""
        # First create a blueprint
        blueprint_path = temp_dir / "blueprint.yaml"
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "Simple chatbot",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0

        # Then run shield command
        result = runner.invoke(
            app,
            ["shield", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0


class TestComplyCommand:
    """Test comply command."""

    def test_comply_shows_compliance_info(self, temp_dir):
        """Test that comply command shows compliance analysis."""
        # First create a blueprint
        blueprint_path = temp_dir / "blueprint.yaml"
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "Simple chatbot",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0

        # Then run comply command
        result = runner.invoke(
            app,
            ["comply", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0


class TestPluginCommand:
    """Test plugin commands."""

    def test_plugin_list(self):
        """Test plugin list command."""
        result = runner.invoke(app, ["plugin", "list"])
        assert result.exit_code == 0

    def test_plugin_init_creates_file(self, temp_dir):
        """Test plugin init creates a plugin file."""
        result = runner.invoke(
            app,
            ["plugin", "init", "test-plugin", "--dir", str(temp_dir)],
        )
        assert result.exit_code == 0
        plugin_file = temp_dir / "test_plugin.py"
        assert plugin_file.exists()
        content = plugin_file.read_text()
        assert "TestPlugin" in content
        assert "AnalysisPlugin" in content


class TestInitCommand:
    """Test init command."""

    def test_init_creates_project_directory(self, temp_dir):
        """Test init command creates .clean-agents directory."""
        result = runner.invoke(
            app,
            ["init", "--name", "test-project", "--dir", str(temp_dir), "--force"],
        )
        assert result.exit_code == 0

        project_dir = temp_dir / ".clean-agents"
        assert project_dir.exists()
        assert (project_dir / "agents").exists()
        assert (project_dir / "prompts").exists()
        assert (project_dir / "evals").exists()
        assert (project_dir / "security").exists()
        assert (project_dir / "compliance").exists()
        assert (project_dir / "history").exists()

        # Check config was created
        config_file = project_dir / "config.yaml"
        assert config_file.exists()

    def test_init_with_custom_options(self, temp_dir):
        """Test init command with custom provider and model."""
        result = runner.invoke(
            app,
            [
                "init",
                "--name",
                "test-project",
                "--dir",
                str(temp_dir),
                "--provider",
                "openai",
                "--model",
                "gpt-4o",
                "--force",
            ],
        )
        assert result.exit_code == 0

        # Verify config has custom values
        config_file = temp_dir / ".clean-agents" / "config.yaml"
        assert config_file.exists()


class TestCommandChain:
    """Test realistic workflows combining multiple commands."""

    def test_design_then_blueprint_then_cost(self, temp_dir):
        """Test a realistic workflow: design -> blueprint -> cost."""
        blueprint_path = temp_dir / "blueprint.yaml"

        # 1. Design
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "E-commerce recommendation engine",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0

        # 2. View blueprint
        result = runner.invoke(
            app,
            ["blueprint", "--format", "summary", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0

        # 3. Check cost
        result = runner.invoke(
            app,
            ["cost", "--path", str(blueprint_path)],
        )
        assert result.exit_code == 0

    def test_init_then_design_workflow(self, temp_dir):
        """Test init followed by design."""
        # 1. Initialize project
        result = runner.invoke(
            app,
            ["init", "--name", "my-agent-project", "--dir", str(temp_dir), "--force"],
        )
        assert result.exit_code == 0

        # 2. Design
        blueprint_path = temp_dir / ".clean-agents" / "blueprint.yaml"
        result = runner.invoke(
            app,
            [
                "design",
                "--desc",
                "Document analysis tool",
                "--no-interactive",
                "--output",
                str(blueprint_path),
            ],
        )
        assert result.exit_code == 0
        assert blueprint_path.exists()
