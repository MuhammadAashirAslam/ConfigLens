"""Unit tests for terminal and JSON reporting and exit code evaluations."""

import json
from pathlib import Path
from click.testing import CliRunner

from configlens.cli import main
from configlens.models import Category, DiscoveredFile, Finding, Severity
from configlens.reporters.json_reporter import build_json_report, render_json_report
from configlens.reporters.terminal import render_terminal_report


def test_build_json_report_structure(tmp_path: Path):
    """Verify build_json_report produces complete schema with threshold violations."""
    target = tmp_path / "repo"
    df = DiscoveredFile(
        path=target / "Dockerfile",
        category=Category.DOCKERFILE,
        relative_path=Path("Dockerfile"),
        size_bytes=120,
    )
    finding = Finding(
        rule_id="dockerfile-latest-tag",
        title="Using latest tag",
        severity=Severity.HIGH,
        category=Category.DOCKERFILE,
        file_path=target / "Dockerfile",
        line_number=1,
        message="Uses latest tag",
        suggested_fix="Pin tag",
    )

    # 1. Threshold is critical -> should pass
    report_crit = build_json_report(target, [df], [finding], fail_on=Severity.CRITICAL)
    assert report_crit["passed"] is True
    assert report_crit["summary"]["total_findings"] == 1
    assert report_crit["summary"]["threshold_violations"] == 0
    assert report_crit["summary"]["high"] == 1

    # 2. Threshold is high -> should fail
    report_high = build_json_report(target, [df], [finding], fail_on=Severity.HIGH)
    assert report_high["passed"] is False
    assert report_high["summary"]["threshold_violations"] == 1

    # Check json rendering string
    json_str = render_json_report(target, [df], [finding], fail_on=Severity.HIGH)
    parsed_json = json.loads(json_str)
    assert parsed_json["fail_on_threshold"] == "high"


def test_render_terminal_report_exit_codes(tmp_path: Path):
    """Verify render_terminal_report returns 0 when clean or below threshold, 1 when threshold met."""
    target = tmp_path / "repo"
    df = DiscoveredFile(
        path=target / "Dockerfile",
        category=Category.DOCKERFILE,
        relative_path=Path("Dockerfile"),
        size_bytes=100,
    )
    med_finding = Finding(
        rule_id="dockerfile-missing-healthcheck",
        title="Missing healthcheck",
        severity=Severity.MEDIUM,
        category=Category.DOCKERFILE,
        file_path=target / "Dockerfile",
        line_number=2,
        message="Missing healthcheck",
        suggested_fix="Add healthcheck",
    )

    # Empty findings -> 0
    assert render_terminal_report(target, [df], [], fail_on=Severity.HIGH) == 0

    # Medium finding with high threshold -> 0
    assert render_terminal_report(target, [df], [med_finding], fail_on=Severity.HIGH) == 0

    # Medium finding with medium threshold -> 1
    assert render_terminal_report(target, [df], [med_finding], fail_on=Severity.MEDIUM) == 1


def test_cli_scan_exit_codes_with_fixtures():
    """Verify CLI scan command returns non-zero code on failing threshold."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    bad_compose = fixtures_dir / "compose" / "bad_compose.yml"
    good_compose = fixtures_dir / "compose" / "good_compose.yml"

    runner = CliRunner()

    # Scanning good file -> exit code 0
    res_good = runner.invoke(main, ["scan", str(good_compose)])
    assert res_good.exit_code == 0
    assert "0 configuration debt findings" in res_good.output

    # Scanning bad file with default threshold (high) -> exit code 1
    res_bad = runner.invoke(main, ["scan", str(bad_compose)])
    assert res_bad.exit_code == 1
    assert "Exit code: 1" in res_bad.output

    # Scanning bad file in JSON mode -> valid JSON and exit code 1
    res_json = runner.invoke(main, ["scan", str(bad_compose), "--format", "json"])
    assert res_json.exit_code == 1
    data = json.loads(res_json.output)
    assert data["passed"] is False
    assert data["summary"]["total_findings"] >= 1
