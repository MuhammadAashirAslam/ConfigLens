"""Integration tests verifying GitHub Action metadata and pre-commit hook configuration."""

from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).parent.parent


def test_action_yml_structure():
    """Verify action.yml contains required GitHub Action composite metadata."""
    action_file = REPO_ROOT / "action.yml"
    assert action_file.is_file()

    content = yaml.safe_load(action_file.read_text(encoding="utf-8"))
    assert content["name"] == "ConfigLens Action"
    assert content["runs"]["using"] == "composite"

    # Verify input definitions
    inputs = content["inputs"]
    assert "path" in inputs
    assert "fail-on" in inputs
    assert "only" in inputs
    assert "ignore" in inputs
    assert "format" in inputs

    # Verify default threshold
    assert inputs["fail-on"]["default"] == "high"


def test_pre_commit_hooks_yml_structure():
    """Verify .pre-commit-hooks.yaml defines the configlens hook correctly."""
    hooks_file = REPO_ROOT / ".pre-commit-hooks.yaml"
    assert hooks_file.is_file()

    content = yaml.safe_load(hooks_file.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert len(content) == 1

    hook = content[0]
    assert hook["id"] == "configlens"
    assert "configlens scan" in hook["entry"]
    assert hook["language"] == "python"
