"""Rule detecting duplicate step names within a GitHub Actions workflow job."""

from pathlib import Path
from typing import Dict, List
from configlens.models import Category, Finding, Severity
from configlens.parsers.workflow_models import WorkflowFile
from configlens.rules.base import Rule, parse_inline_suppressions


class DuplicateStepNamesRule(Rule):
    """Flags duplicate step names within a single workflow job."""

    id = "gha-duplicate-step-names"
    title = "Duplicate step names in job"
    description = "Step names within the same job should be unique to maintain readable and debuggable CI logs."
    severity = Severity.LOW
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: WorkflowFile) -> List[Finding]:
        """Check for repeated step names within jobs."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for job in parsed.jobs.values():
            seen_names: Dict[str, int] = {}

            for step in job.steps:
                if not step.name:
                    continue

                norm_name = step.name.strip().lower()
                if norm_name in seen_names:
                    original_line = seen_names[norm_name]
                    if not self.is_line_suppressed(suppressions, step.line_number):
                        findings.append(
                            self.create_finding(
                                file_path=file_path,
                                line_number=step.line_number,
                                message=f"Duplicate step name '{step.name}' in job '{job.job_id}' (first defined on line {original_line}).",
                                suggested_fix="Assign a unique, descriptive name to distinguish this step in CI execution logs.",
                            )
                        )
                else:
                    seen_names[norm_name] = step.line_number

        return findings
