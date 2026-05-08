"""Rule detecting missing HEALTHCHECK instruction in Dockerfiles."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions


class MissingHealthcheckRule(Rule):
    """Flags Dockerfiles that produce long-running containers without a HEALTHCHECK."""

    id = "dockerfile-missing-healthcheck"
    title = "Missing HEALTHCHECK instruction"
    description = "Production container images should declare a HEALTHCHECK to allow container runtimes to detect unresponsive or unhealthy services."
    severity = Severity.MEDIUM
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Check final stage for HEALTHCHECK instruction."""
        findings: List[Finding] = []
        if not parsed.stages:
            return findings

        suppressions = parse_inline_suppressions(file_path)
        final_stage = parsed.stages[-1]

        # Ignore scratch images
        if final_stage.base_image.strip().lower() == "scratch":
            return findings

        has_healthcheck = False
        has_entrypoint_or_cmd = False

        for inst in final_stage.instructions:
            if inst.instruction == "HEALTHCHECK":
                has_healthcheck = True
            elif inst.instruction in {"CMD", "ENTRYPOINT"}:
                has_entrypoint_or_cmd = True

        if has_entrypoint_or_cmd and not has_healthcheck:
            if not self.is_line_suppressed(suppressions, final_stage.line_number):
                findings.append(
                    self.create_finding(
                        file_path=file_path,
                        line_number=final_stage.line_number,
                        message="Final container image declares entrypoint/cmd but lacks a HEALTHCHECK instruction.",
                        suggested_fix="Add 'HEALTHCHECK CMD curl -f http://localhost/health || exit 1' (or appropriate probe command).",
                    )
                )

        return findings
