"""Unit tests for YAML loader and GitHub Actions workflow parser."""

from pathlib import Path
from configlens.parsers.workflow_parser import parse_workflow_content, parse_workflow_file
from configlens.parsers.yaml_loader import (
    AnnotatedDict,
    AnnotatedList,
    load_yaml_with_line_numbers,
)

SAMPLE_WORKFLOW_YAML = """name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Run linter
        run: flake8 .

  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run test suite
        run: pytest
        env:
          CI: "true"
"""


def test_yaml_loader_preserves_lines():
    """Verify that YAML loader preserves line numbers on mappings and keys."""
    data = load_yaml_with_line_numbers(SAMPLE_WORKFLOW_YAML)
    assert isinstance(data, AnnotatedDict)
    assert data.line_number == 1
    assert data.get_line("jobs") == 8
    assert data["jobs"].get_line("lint") == 9
    assert data["jobs"].get_line("build-and-test") == 18


def test_yaml_loader_malformed_graceful():
    """Verify that malformed YAML does not crash and returns parse error info."""
    bad_yaml = "invalid: [unclosed, mapping: {bad}"
    data = load_yaml_with_line_numbers(bad_yaml)
    assert isinstance(data, AnnotatedDict)
    assert "__parse_error__" in data
    assert data.line_number >= 1


def test_yaml_loader_empty():
    """Verify empty or comment-only YAML returns None."""
    assert load_yaml_with_line_numbers("") is None
    assert load_yaml_with_line_numbers("   \n# comment\n") is None


def test_parse_workflow_structure():
    """Verify workflow parser creates typed WorkflowFile with jobs and steps."""
    wf = parse_workflow_content(SAMPLE_WORKFLOW_YAML)

    assert wf.name == "CI Pipeline"
    assert len(wf.jobs) == 2

    # Check lint job
    lint_job = wf.jobs["lint"]
    assert lint_job.job_id == "lint"
    assert lint_job.runs_on == "ubuntu-latest"
    assert lint_job.timeout_minutes == 15
    assert lint_job.line_number == 9
    assert len(lint_job.steps) == 2

    # Check step line numbers and attributes
    step1 = lint_job.steps[0]
    assert step1.name == "Checkout repository"
    assert step1.uses == "actions/checkout@v4"
    assert step1.line_number == 13

    step2 = lint_job.steps[1]
    assert step2.name == "Run linter"
    assert step2.run == "flake8 ."
    assert step2.line_number == 15

    # Check build-and-test job
    test_job = wf.jobs["build-and-test"]
    assert test_job.line_number == 18
    assert len(test_job.steps) == 2
    assert test_job.steps[0].uses == "actions/checkout@v4"
    assert test_job.steps[0].line_number == 21
    assert test_job.steps[1].env.get("CI") == "true"
    assert test_job.steps[1].line_number == 22


def test_parse_workflow_file_missing():
    """Verify parsing a non-existent file degrades gracefully."""
    wf = parse_workflow_file(Path("non_existent_ci.yml"))
    assert wf.line_number == 1
    assert len(wf.jobs) == 0


def test_parse_workflow_malformed():
    """Verify parsing malformed workflow YAML degrades gracefully."""
    bad_wf = "name: Bad\njobs: [not a dict"
    wf = parse_workflow_content(bad_wf)
    assert wf.line_number >= 1
    assert len(wf.jobs) == 0
