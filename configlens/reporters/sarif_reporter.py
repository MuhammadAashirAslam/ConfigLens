"""SARIF v2.1.0 output generator for GitHub code scanning integration."""

import json
from pathlib import Path
from typing import Any, Dict, List
from configlens import __version__
from configlens.discovery import DiscoveredFile
from configlens.models import Finding, Severity

SARIF_SCHEMA_URI = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
)

SEVERITY_TO_SARIF_LEVEL: Dict[Severity, str] = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
}


def build_sarif_report(
    target_dir: Path,
    files: List[DiscoveredFile],
    findings: List[Finding],
    fail_on_severity: Severity = Severity.HIGH,
) -> Dict[str, Any]:
    """Construct a standard SARIF v2.1.0 dictionary representation from findings."""
    rules_dict: Dict[str, Dict[str, Any]] = {}
    results_list: List[Dict[str, Any]] = []

    for finding in findings:
        rule_id = finding.rule_id
        if rule_id not in rules_dict:
            rules_dict[rule_id] = {
                "id": rule_id,
                "name": "".join(word.capitalize() for word in rule_id.split("-")),
                "shortDescription": {
                    "text": finding.title,
                },
                "fullDescription": {
                    "text": finding.title,
                },
                "help": {
                    "text": finding.suggested_fix,
                    "markdown": f"**Suggested Fix:** {finding.suggested_fix}",
                },
                "properties": {
                    "category": finding.category.value,
                    "defaultSeverity": finding.severity.value,
                    "tags": ["DevOps", "TechnicalDebt", finding.category.value],
                },
            }

        # Calculate relative path
        try:
            rel_path = finding.file_path.relative_to(target_dir).as_posix()
        except ValueError:
            rel_path = finding.file_path.as_posix()

        sarif_level = SEVERITY_TO_SARIF_LEVEL.get(finding.severity, "warning")

        result_item: Dict[str, Any] = {
            "ruleId": rule_id,
            "level": sarif_level,
            "message": {
                "text": finding.message,
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": rel_path,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": max(1, finding.line_number),
                            "startColumn": finding.column if finding.column else 1,
                        },
                    }
                }
            ],
        }

        if finding.suggested_fix:
            result_item["fixes"] = [
                {
                    "description": {
                        "text": finding.suggested_fix,
                    }
                }
            ]

        results_list.append(result_item)

    sarif_doc = {
        "$schema": SARIF_SCHEMA_URI,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ConfigLens",
                        "version": __version__,
                        "informationUri": "https://github.com/MuhammadAashirAslam/ConfigLens",
                        "rules": list(rules_dict.values()),
                    }
                },
                "results": results_list,
            }
        ],
    }

    return sarif_doc


def render_sarif_report(
    target_dir: Path,
    files: List[DiscoveredFile],
    findings: List[Finding],
    fail_on_severity: Severity = Severity.HIGH,
) -> str:
    """Render findings as a formatted SARIF v2.1.0 JSON string."""
    data = build_sarif_report(target_dir, files, findings, fail_on_severity)
    return json.dumps(data, indent=2)
