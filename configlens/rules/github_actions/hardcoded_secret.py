"""Rule detecting hardcoded secrets and tokens in GitHub Actions workflows."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.workflow_models import WorkflowFile
from configlens.rules.base import Rule, parse_inline_suppressions

SECRET_PATTERNS = [
    (re.compile(r"\b(ghp_[A-Za-z0-9]{36})\b"), "GitHub Personal Access Token"),
    (re.compile(r"\b(github_pat_[A-Za-z0-9_]{82})\b"), "Fine-grained GitHub PAT"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "AWS Access Key ID"),
    (re.compile(r"\b(?:api[_-]?key|secret|password|auth[_-]?token)\s*[:=]\s*['\"]([^${}\s'\"]{8,})['\"]", re.IGNORECASE), "API Key / Password"),
]

IGNORED_PLACEHOLDERS = {"example", "placeholder", "dummy", "test", "fake", "your_secret", "changeme"}


class PlaintextHardcodedSecretRule(Rule):
    """Flags plaintext hardcoded secrets or API tokens in workflow files."""

    id = "gha-hardcoded-secret"
    title = "Plaintext hardcoded secret"
    description = "Secrets and access credentials must not be stored in plaintext within workflow files."
    severity = Severity.CRITICAL
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: WorkflowFile) -> List[Finding]:
        """Inspect workflow environment variables and run commands for leaked credentials."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for job in parsed.jobs.values():
            for step in job.steps:
                # 1. Check step env values
                for env_k, env_v in step.env.items():
                    if isinstance(env_v, str):
                        for pattern, secret_type in SECRET_PATTERNS:
                            match = pattern.search(env_v)
                            if match:
                                val = match.group(1)
                                if val.lower() not in IGNORED_PLACEHOLDERS and not val.startswith("${{"):
                                    if not self.is_line_suppressed(suppressions, step.line_number):
                                        findings.append(
                                            self.create_finding(
                                                file_path=file_path,
                                                line_number=step.line_number,
                                                message=f"Possible plaintext {secret_type} found in env variable '{env_k}'.",
                                                suggested_fix="Reference credential securely via GitHub Secrets (e.g., ${{ secrets.MY_TOKEN }}).",
                                            )
                                        )

                # 2. Check step run command
                run_cmd = step.run or ""
                for pattern, secret_type in SECRET_PATTERNS:
                    match = pattern.search(run_cmd)
                    if match:
                        val = match.group(1)
                        if val.lower() not in IGNORED_PLACEHOLDERS and not val.startswith("${{"):
                            if not self.is_line_suppressed(suppressions, step.line_number):
                                findings.append(
                                    self.create_finding(
                                        file_path=file_path,
                                        line_number=step.line_number,
                                        message=f"Possible plaintext {secret_type} found in step run command.",
                                        suggested_fix="Extract token to a GitHub Secret and pass via environment variable.",
                                    )
                                )

        return findings
