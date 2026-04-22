"""Tests for `clean-agents skill-sync` — installs the versioned skill bundle."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from clean_agents.cli.main import app

runner = CliRunner()


def test_skill_sync_installs_bundle_into_empty_target(tmp_path: Path):
    target = tmp_path / "skills" / "clean-agents"
    result = runner.invoke(app, ["skill-sync", "--target", str(target)])
    assert result.exit_code == 0, result.stdout

    # SKILL.md + all references landed
    assert (target / "SKILL.md").is_file()
    assert (target / "references" / "crafters.md").is_file()
    assert (target / "references" / "taxonomy.md").is_file()

    # Content round-trips
    content = (target / "SKILL.md").read_text(encoding="utf-8")
    assert "## Crafters:" in content


def test_skill_sync_without_force_refuses_to_overwrite_modified_file(tmp_path: Path):
    target = tmp_path / "skills" / "clean-agents"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("# user's local edits\n", encoding="utf-8")

    result = runner.invoke(app, ["skill-sync", "--target", str(target)])
    # Non-zero exit to make CI fail loudly when someone runs sync on a modified target
    assert result.exit_code != 0
    assert "--force" in result.stdout or "force" in result.stdout.lower()
    # File remains untouched
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "# user's local edits\n"


def test_skill_sync_with_force_overwrites(tmp_path: Path):
    target = tmp_path / "skills" / "clean-agents"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("# stale content\n", encoding="utf-8")

    result = runner.invoke(app, ["skill-sync", "--target", str(target), "--force"])
    assert result.exit_code == 0, result.stdout
    new_content = (target / "SKILL.md").read_text(encoding="utf-8")
    assert new_content != "# stale content\n"
    assert "## Crafters:" in new_content


def test_skill_sync_dry_run_writes_nothing(tmp_path: Path):
    target = tmp_path / "skills" / "clean-agents"
    result = runner.invoke(app, ["skill-sync", "--target", str(target), "--dry-run"])
    assert result.exit_code == 0, result.stdout
    # Target dir is NOT created during dry-run
    assert not target.exists()
    # Output reports what would happen
    assert "SKILL.md" in result.stdout


def test_skill_sync_unchanged_files_reported_as_such(tmp_path: Path):
    target = tmp_path / "skills" / "clean-agents"
    # First run installs cleanly
    r1 = runner.invoke(app, ["skill-sync", "--target", str(target)])
    assert r1.exit_code == 0
    # Second run finds everything identical
    r2 = runner.invoke(app, ["skill-sync", "--target", str(target)])
    assert r2.exit_code == 0, r2.stdout
    # Message should signal no-op, not fake update
    lower = r2.stdout.lower()
    assert "unchanged" in lower or "up to date" in lower or "no changes" in lower


def test_skill_sync_creates_nested_references_dir(tmp_path: Path):
    target = tmp_path / "deep" / "path" / "clean-agents"
    result = runner.invoke(app, ["skill-sync", "--target", str(target)])
    assert result.exit_code == 0, result.stdout
    assert (target / "references").is_dir()
    assert (target / "references" / "crafters.md").is_file()
