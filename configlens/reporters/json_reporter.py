"""Machine-readable JSON reporting conforming to documented ConfigLens schema."""

import json
from pathlib import Path
from typing import Any, Dict, List
from configlens import __version__
from configlens.models import DiscoveredFile, Finding, Severity


def build_json_report(
    target_path: Path,
    discovered_files: List[DiscoveredFile],
    findings: List[Finding],
    fail_on: Severity,
) -> Dict[str, Any]:
    """Construct stable JSON report dictionary."""
    critical_cnt = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    high_cnt = sum(1 for f in findings if f.severity == Severity.HIGH)
    medium_cnt = sum(1 for f in findings if f.severity == Severity.MEDIUM)
    low_cnt = sum(1 for f in findings if f.severity == Severity.LOW)

    threshold_rank = fail_on.rank
    failing_count = sum(1 for f in findings if f.severity.rank >= threshold_rank)
    passed = failing_count == 0

    return {
        "version": __version__,
        "target": str(target_path.resolve()),
        "fail_on_threshold": fail_on.value,
        "passed": passed,
        "discovered_files_count": len(discovered_files),
        "files": [f.to_dict() for f in discovered_files],
        "findings": [f.to_dict() for f in findings],
        "summary": {
            "total_findings": len(findings),
            "critical": critical_cnt,
            "high": high_cnt,
            "medium": medium_cnt,
            "low": low_cnt,
            "threshold_violations": failing_count,
        },
    }


def render_json_report(
    target_path: Path,
    discovered_files: List[DiscoveredFile],
    findings: List[Finding],
    fail_on: Severity,
    indent: int = 2,
) -> str:
    """Serialize JSON report to string."""
    report = build_json_report(target_path, discovered_files, findings, fail_on)
    return json.dumps(report, indent=indent)
