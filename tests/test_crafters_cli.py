from pathlib import Path

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


def test_validate_good_skill_succeeds():
    fixture = Path("tests/fixtures/crafters/skill/good-skill")
    result = runner.invoke(app, ["skill", "validate", str(fixture)])
    assert result.exit_code == 0, result.stdout
    # good-skill passes because it has no CRITICAL or blocking findings (only medium L2 warning)
    assert "good-skill" in result.stdout


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
    parsed = json.loads(result.stdout.strip())  # Parse entire output as JSON
    assert "findings" in parsed


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
