"""Rule detecting missing or overly broad permissions in GitHub Actions workflows."""

from pathlib import Path
from typing import Any, List
from configlens.models import Category, Finding, Severity
from configlens.parsers.workflow_models import WorkflowFile
from configlens.rules.base import Rule, parse_inline_suppressions


class BroadPermissionsRule(Rule):
    """Flags workflows or jobs that lack explicit least-privilege permissions."""

    id = "gha-broad-permissions"
    title = "Overly broad or missing permissions"
    description = "Workflows should specify explicit, least-privilege permissions rather than relying on default write access or write-all."
    severity = Severity.HIGH
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: WorkflowFile) -> List[Finding]:
        """Check for missing permissions or write-all configurations."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        wf_perms = parsed.permissions

        # 1. Check top-level write-all
        if wf_perms == "write-all":
            if not self.is_line_suppressed(suppressions, parsed.line_number):
                findings.append(
                    self.create_finding(
                        file_path=file_path,
                        line_number=parsed.line_number,
                        message="Workflow declares 'permissions: write-all', granting broad write access to GITHUB_TOKEN.",
                        suggested_fix="Scope permissions to minimal requirements (e.g., permissions: contents: read).",
                    )
                )

        # 2. Check if permissions block is completely missing from top-level and all jobs
        has_any_perms = wf_perms is not None
        for job in parsed.jobs.values():
            if job.permissions is not None:
                has_any_perms = True
            if job.permissions == "write-all":
                if not self.is_line_suppressed(suppressions, job.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=job.line_number,
                            message=f"Job '{job.job_id}' declares 'permissions: write-all'.",
                            suggested_fix="Specify least-privilege scopes (e.g., permissions: contents: read).",
                        )
                    )

        if not has_any_perms and parsed.jobs:
            if not self.is_line_suppressed(suppressions, parsed.line_number):
                findings.append(
                    self.create_finding(
                        file_path=file_path,
                        line_number=parsed.line_number,
                        message="Workflow lacks an explicit 'permissions:' declaration, inheriting default repository permissions.",
                        suggested_fix="Add a top-level 'permissions: contents: read' block to enforce least-privilege access.",
                    )
                )

        return findings
