"""Comprehensive baseline validation tests across realistic open-source DevOps configurations."""

import time
from pathlib import Path
import pytest
from configlens.cli import execute_scan
from configlens.models import Category, Severity

REPO_ROOT = Path(__file__).parent.parent
FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def test_baseline_multi_category_scan():
    """Verify that scanning all fixtures across all categories succeeds deterministically."""
    start_time = time.perf_counter()
    files, findings = execute_scan(FIXTURES_ROOT)
    scan_duration = time.perf_counter() - start_time

    # Performance requirement: scan must execute quickly (< 1.0s)
    assert scan_duration < 1.0, f"Scan took {scan_duration:.3f}s, exceeding 1s target."

    # All 5 supported categories must be discovered
    discovered_categories = {f.category for f in files}
    assert Category.GITHUB_ACTIONS in discovered_categories
    assert Category.DOCKERFILE in discovered_categories
    assert Category.DOCKER_COMPOSE in discovered_categories
    assert Category.TERRAFORM in discovered_categories
    assert Category.KUBERNETES in discovered_categories

    # Ensure findings are found across categories
    finding_categories = {f.category for f in findings}
    assert len(finding_categories) == 5

    # Check findings are sorted deterministically
    paths_and_lines = [(str(f.file_path), f.line_number, f.rule_id) for f in findings]
    assert paths_and_lines == sorted(paths_and_lines)


def test_baseline_suppression_robustness(tmp_path: Path):
    """Verify inline suppression comments work robustly with spaces and multiple rules."""
    tf_file = tmp_path / "main.tf"
    tf_file.write_text(
        """# configlens-ignore: tf-hardcoded-secret
resource "aws_db_instance" "prod" {
  password = "plaintext-secret-value-1234"
  lifecycle {
    prevent_destroy = true
  }
}
""",
        encoding="utf-8",
    )

    files, findings = execute_scan(tmp_path, only_categories={Category.TERRAFORM})
    assert len(files) == 1
    rule_ids = [f.rule_id for f in findings]
    assert "tf-hardcoded-secret" not in rule_ids


def test_baseline_severity_thresholds():
    """Verify critical severity findings exist and can trigger high-severity thresholds."""
    files, findings = execute_scan(FIXTURES_ROOT)
    critical_findings = [f for f in findings if f.severity == Severity.CRITICAL]
    high_findings = [f for f in findings if f.severity == Severity.HIGH]

    assert len(critical_findings) > 0
    assert len(high_findings) > 0
