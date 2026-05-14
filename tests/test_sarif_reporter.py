"""Unit tests for SARIF v2.1.0 reporting."""

import json
from pathlib import Path
from click.testing import CliRunner
from configlens.cli import main
from configlens.discovery import DiscoveredFile
from configlens.models import Category, Finding, Severity
from configlens.reporters.sarif_reporter import build_sarif_report


def test_build_sarif_report_structure(tmp_path: Path):
    """Verify that build_sarif_report produces a conforming SARIF v2.1.0 document."""
    file_path = tmp_path / "Dockerfile"
    files = [DiscoveredFile(path=file_path, relative_path=Path("Dockerfile"), category=Category.DOCKERFILE)]
    findings = [
        Finding(
            rule_id="dockerfile-running-as-root",
            title="Container running as root",
            severity=Severity.CRITICAL,
            category=Category.DOCKERFILE,
            file_path=file_path,
            line_number=14,
            message="Dockerfile does not specify a non-root USER instruction.",
            suggested_fix="Add 'USER <non-root-user>' before CMD or ENTRYPOINT.",
        )
    ]

    report = build_sarif_report(tmp_path, files, findings, Severity.HIGH)

    assert report["version"] == "2.1.0"
    assert "$schema" in report
    assert len(report["runs"]) == 1

    run = report["runs"][0]
    driver = run["tool"]["driver"]
    assert driver["name"] == "ConfigLens"
    assert len(driver["rules"]) == 1
    assert driver["rules"][0]["id"] == "dockerfile-running-as-root"

    assert len(run["results"]) == 1
    res = run["results"][0]
    assert res["ruleId"] == "dockerfile-running-as-root"
    assert res["level"] == "error"
    assert res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "Dockerfile"
    assert res["locations"][0]["physicalLocation"]["region"]["startLine"] == 14
    assert len(res["fixes"]) == 1


def test_sarif_cli_scan_execution(tmp_path: Path):
    """Verify CLI --format sarif option executes and outputs valid JSON."""
    df_file = tmp_path / "Dockerfile"
    df_file.write_text("FROM alpine:3.19\nUSER appuser\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--format", "sarif", "--fail-on", "critical"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["version"] == "2.1.0"
    assert len(data["runs"]) == 1
    assert data["runs"][0]["tool"]["driver"]["name"] == "ConfigLens"
