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
