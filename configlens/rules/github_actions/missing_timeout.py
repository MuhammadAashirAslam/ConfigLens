"""Rule detecting missing job timeout in GitHub Actions workflows."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.workflow_models import WorkflowFile
from configlens.rules.base import Rule, parse_inline_suppressions


class MissingJobTimeoutRule(Rule):
    """Flags workflow jobs missing an explicit timeout-minutes definition."""

    id = "gha-missing-timeout"
    title = "Missing job timeout"
    description = "Jobs without an explicit timeout-minutes can stall and exhaust workflow runner queue capacity or consume billed minutes."
    severity = Severity.MEDIUM
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: WorkflowFile) -> List[Finding]:
        """Check all workflow jobs for missing timeout-minutes."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for job in parsed.jobs.values():
            if job.timeout_minutes is None:
                if not self.is_line_suppressed(suppressions, job.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=job.line_number,
                            message=f"Job '{job.job_id}' does not specify 'timeout-minutes:'.",
                            suggested_fix="Add 'timeout-minutes: 30' (or appropriate duration) to the job.",
                        )
                    )

        return findings
