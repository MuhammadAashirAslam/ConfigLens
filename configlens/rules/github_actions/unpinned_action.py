"""Rule detecting GitHub Actions unpinned to a full commit SHA."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.workflow_models import WorkflowFile
from configlens.rules.base import Rule, parse_inline_suppressions

SHA_PATTERN = re.compile(r"@[0-9a-fA-F]{40}$")


class UnpinnedActionVersionRule(Rule):
    """Flags GitHub Actions references not pinned to an immutable 40-character commit SHA."""

    id = "gha-unpinned-action"
    title = "Unpinned action version"
    description = "Action versions should be pinned to a full commit SHA to guarantee reproducibility and prevent supply-chain tampering."
    severity = Severity.HIGH
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: WorkflowFile) -> List[Finding]:
        """Check all workflow steps for unpinned actions."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for job in parsed.jobs.values():
            for step in job.steps:
                uses = step.uses
                if not uses:
                    continue

                # Skip local actions and docker container actions
                if uses.startswith("./") or uses.startswith("docker://"):
                    continue

                # Must contain @ and 40-char SHA
                if not SHA_PATTERN.search(uses):
                    if not self.is_line_suppressed(suppressions, step.line_number):
                        action_name = uses.split("@")[0] if "@" in uses else uses
                        findings.append(
                            self.create_finding(
                                file_path=file_path,
                                line_number=step.line_number,
                                message=f"Action '{uses}' is not pinned to a full 40-character commit SHA.",
                                suggested_fix=f"Pin '{action_name}' to a full commit SHA (e.g., uses: {action_name}@<commit-sha>).",
                            )
                        )

        return findings
