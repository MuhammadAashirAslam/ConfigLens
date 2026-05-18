"""Tests for CLI entrypoint and basic flags."""

import json
from pathlib import Path
from click.testing import CliRunner
from configlens import __version__
from configlens.cli import main


def test_cli_version():
    """Verify that --version returns the correct version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert f"configlens, version {__version__}" in result.output


def test_cli_help():
    """Verify that --help displays the help banner."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ConfigLens" in result.output
    assert "Show this message and exit." in result.output


def test_cli_scan_terminal(tmp_path: Path):
    """Verify scan command produces terminal summary report."""
    (tmp_path / "Dockerfile").write_text("FROM alpine:3.18\nUSER 10001\n", encoding="utf-8")
    (tmp_path / "main.tf").write_text('variable "foo" {}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--fail-on", "critical"])
    assert result.exit_code == 0
    assert "ConfigLens" in result.output


def test_cli_scan_json(tmp_path: Path):
    """Verify scan command produces valid JSON report."""
    (tmp_path / "Dockerfile").write_text("FROM alpine:3.18\nUSER 10001\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--format", "json", "--fail-on", "critical"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["version"] == __version__
    assert data["discovered_files_count"] == 1
    assert data["files"][0]["category"] == "dockerfile"
    assert data["passed"] is True


def test_cli_scan_only_filter(tmp_path: Path):
    """Verify scan command respects --only filter."""
    (tmp_path / "Dockerfile").write_text("FROM alpine:3.18\nUSER 10001\n", encoding="utf-8")
    (tmp_path / "main.tf").write_text('variable "foo" {}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--only", "terraform", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["discovered_files_count"] == 1
    assert data["files"][0]["category"] == "terraform"


def test_cli_scan_empty_directory(tmp_path: Path):
    """Verify scan command handles directory with no configs gracefully."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(empty_dir)])
    assert result.exit_code == 0
    assert "No supported DevOps configuration files discovered" in result.output
