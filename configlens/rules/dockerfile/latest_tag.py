"""Rule detecting unpinned or :latest base image tags in Dockerfiles."""

import re
from pathlib import Path
from typing import List, Set
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions


class DockerfileLatestTagRule(Rule):
    """Flags Dockerfile FROM instructions referencing :latest or unpinned image tags."""

    id = "dockerfile-latest-tag"
    title = "Using latest or unpinned base image tag"
    description = "Base images should specify an explicit version tag or digest rather than :latest or no tag to ensure reproducible builds."
    severity = Severity.HIGH
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Check all FROM instructions for latest or missing tags."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        known_stage_names: Set[str] = {
            s.name.lower() for s in parsed.stages if s.name
        }

        for stage in parsed.stages:
            base_image = stage.base_image.strip()

            # Handle --platform flag in FROM
            if base_image.startswith("--platform"):
                parts = base_image.split()
                if len(parts) > 1:
                    base_image = parts[1]

            image_name = base_image.lower()

            # Skip scratch and references to previous build stages
            if image_name in {"scratch"} or image_name in known_stage_names:
                continue

            is_latest = False
            # Tag is explicitly :latest
            if image_name.endswith(":latest") or ":latest@" in image_name:
                is_latest = True
            # No tag and no digest specified
            elif ":" not in image_name and "@" not in image_name:
                is_latest = True

            if is_latest:
                if not self.is_line_suppressed(suppressions, stage.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=stage.line_number,
                            message=f"Base image '{stage.base_image}' uses ':latest' or lacks an explicit version tag.",
                            suggested_fix=f"Pin base image '{stage.base_image}' to an explicit immutable tag or digest (e.g., {stage.base_image.split(':')[0]}:<version>).",
                        )
                    )

        return findings
