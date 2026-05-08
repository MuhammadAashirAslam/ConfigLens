"""Rule detecting Dockerfile containers running as root."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions


class DockerfileRunningAsRootRule(Rule):
    """Flags Dockerfiles that do not define a non-root USER in the final image stage."""

    id = "dockerfile-running-as-root"
    title = "Running container as root"
    description = "Containers should run as a non-root user to mitigate privilege-escalation vulnerabilities and follow security best practices."
    severity = Severity.CRITICAL
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Check the final build stage for non-root USER instruction."""
        findings: List[Finding] = []
        if not parsed.stages:
            return findings

        suppressions = parse_inline_suppressions(file_path)
        final_stage = parsed.stages[-1]

        # Scan instructions in the final stage
        last_user_inst = None
        for inst in final_stage.instructions:
            if inst.instruction == "USER":
                last_user_inst = inst

        is_root = False
        target_line = final_stage.line_number

        if last_user_inst is None:
            is_root = True
        else:
            user_arg = last_user_inst.arguments.strip().lower()
            target_line = last_user_inst.line_number
            if user_arg in {"root", "0", "0:0"}:
                is_root = True

        if is_root:
            if not self.is_line_suppressed(suppressions, target_line):
                findings.append(
                    self.create_finding(
                        file_path=file_path,
                        line_number=target_line,
                        message="Final container stage executes as root (no non-root USER instruction specified).",
                        suggested_fix="Create a non-root user and switch with 'USER appuser' or 'USER 10001' before CMD/ENTRYPOINT.",
                    )
                )

        return findings
