"""Rule detecting missing dependency caching in GitHub Actions workflows."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.workflow_models import WorkflowFile, WorkflowJob
from configlens.rules.base import Rule, parse_inline_suppressions

PKG_INSTALL_CMDS = re.compile(
    r"\b(npm\s+(?:install|ci)|yarn(?:\s+install)?|pnpm\s+install|pip\s+install|poetry\s+install|pipenv\s+install|mvn\s+|gradle\s+|cargo\s+build)\b"
)
SETUP_ACTIONS_SUPPORTING_CACHE = {
    "actions/setup-node",
    "actions/setup-python",
    "actions/setup-go",
    "actions/setup-java",
}


class MissingDependencyCachingRule(Rule):
    """Flags workflow jobs installing dependencies without configuring build/package caching."""

    id = "gha-missing-caching"
    title = "Missing dependency caching"
    description = "Workflows that install dependencies or compile packages should utilize caching to decrease CI runtime and reduce network strain."
    severity = Severity.MEDIUM
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: WorkflowFile) -> List[Finding]:
        """Check if jobs with dependency install steps lack caching."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for job in parsed.jobs.values():
            has_cache_step = False
            install_step_line: int = 0
            install_step_name = ""

            for step in job.steps:
                uses = step.uses or ""
                uses_base = uses.split("@")[0].lower() if "@" in uses else uses.lower()

                # Check if actions/cache is explicitly used
                if uses_base == "actions/cache":
                    has_cache_step = True

                # Check if setup action has cache configured
                if uses_base in SETUP_ACTIONS_SUPPORTING_CACHE:
                    if step.with_args.get("cache"):
                        has_cache_step = True

                # Check if this step runs a package manager installation
                run_cmd = step.run or ""
                if PKG_INSTALL_CMDS.search(run_cmd) and not install_step_line:
                    install_step_line = step.line_number
                    install_step_name = step.name or "Install dependencies"

            if install_step_line and not has_cache_step:
                if not self.is_line_suppressed(suppressions, install_step_line):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=install_step_line,
                            message=f"Job '{job.job_id}' installs dependencies in step '{install_step_name}' but does not configure caching.",
                            suggested_fix="Enable caching in setup action (e.g., cache: 'npm') or add an actions/cache step.",
                        )
                    )

        return findings
