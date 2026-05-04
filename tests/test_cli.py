"""Tests for CLI entrypoint and basic flags."""

from click.testing import CliRunner
from configlens.cli import main


def test_cli_version():
    """Verify that --version returns the correct version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "configlens, version 0.1.0" in result.output


def test_cli_help():
    """Verify that --help displays the help banner."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ConfigLens" in result.output
    assert "Show this message and exit." in result.output
