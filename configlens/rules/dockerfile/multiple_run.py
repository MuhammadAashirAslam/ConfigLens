"""Rule detecting multiple consecutive RUN instructions in Dockerfiles."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions


class MultipleRunLayersRule(Rule):
    """Flags consecutive RUN instructions that should be chained together."""

    id = "dockerfile-multiple-run-layers"
    title = "Multiple consecutive RUN instructions"
    description = "Consecutive RUN instructions create additional filesystem layers and increase container image size. Chain them with '&&'."
    severity = Severity.LOW
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Check for consecutive RUN instructions in each build stage."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for idx, stage in enumerate(parsed.stages):
            # In multi-stage builds, intermediate builder stages (not the final stage) often
            # deliberately separate dependency installation from compilation for layer caching.
            is_intermediate = (idx < len(parsed.stages) - 1) and bool(stage.name)
            if is_intermediate:
                continue

            prev_was_run = False
            for inst in stage.instructions:
                if inst.instruction == "RUN":
                    if prev_was_run:
                        if not self.is_line_suppressed(suppressions, inst.line_number):
                            findings.append(
                                self.create_finding(
                                    file_path=file_path,
                                    line_number=inst.line_number,
                                    message="Consecutive RUN instruction creates unnecessary intermediate image layer.",
                                    suggested_fix="Combine consecutive RUN instructions using '&& \\' to reduce image layers.",
                                )
                            )
                    prev_was_run = True
                else:
                    prev_was_run = False

        return findings
