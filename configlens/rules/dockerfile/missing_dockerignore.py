"""Rule detecting broad context copying without a .dockerignore file."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions

BROAD_COPY_PATTERN = re.compile(r"^\s*(?:--[^\s]+\s+)*(\.|\./)\s+", re.IGNORECASE)


class MissingDockerignoreRule(Rule):
    """Flags broad context copy instructions (COPY . .) when no .dockerignore file is present."""

    id = "dockerfile-missing-dockerignore"
    title = "Missing .dockerignore file for broad context copy"
    description = "Copying the entire context root without a .dockerignore file risks copying credentials, local caches, and git history into the build."
    severity = Severity.MEDIUM
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Check if COPY . instructions exist in a directory lacking .dockerignore."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        # Check if .dockerignore exists in the Dockerfile's parent or repository root
        dockerignore_exists = False
        dir_path = file_path.resolve().parent
        for candidate in [dir_path / ".dockerignore", dir_path.parent / ".dockerignore"]:
            if candidate.is_file():
                dockerignore_exists = True
                break

        if dockerignore_exists:
            return findings

        for inst in parsed.instructions:
            if inst.instruction in {"COPY", "ADD"}:
                # Exclude multi-stage copy like COPY --from=...
                if "--from=" in inst.arguments:
                    continue

                if BROAD_COPY_PATTERN.search(inst.arguments.strip()):
                    if not self.is_line_suppressed(suppressions, inst.line_number):
                        findings.append(
                            self.create_finding(
                                file_path=file_path,
                                line_number=inst.line_number,
                                message=f"{inst.instruction} copies entire directory context without a .dockerignore file.",
                                suggested_fix="Add a .dockerignore file to exclude sensitive or unnecessary files (.git, .env, __pycache__).",
                            )
                        )

        return findings
