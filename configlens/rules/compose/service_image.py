"""Rule detecting :latest or unpinned image tags in Docker Compose services."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.compose_models import ComposeFile
from configlens.rules.base import Rule, parse_inline_suppressions


class ComposeLatestTagRule(Rule):
    """Flags Docker Compose service images using :latest or lacking version pinning."""

    id = "compose-latest-tag"
    title = "Service image uses :latest or unpinned tag"
    description = "Service images should specify an explicit version tag or digest rather than :latest or no tag."
    severity = Severity.HIGH
    category = Category.DOCKER_COMPOSE

    def check(self, file_path: Path, parsed: ComposeFile) -> List[Finding]:
        """Check all services for unpinned image tags."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for svc in parsed.services.values():
            image = svc.image
            if not image:
                continue

            image_str = image.strip().lower()
            is_latest = False
            if image_str.endswith(":latest") or ":latest@" in image_str:
                is_latest = True
            elif ":" not in image_str and "@" not in image_str:
                is_latest = True

            if is_latest:
                if not self.is_line_suppressed(suppressions, svc.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=svc.line_number,
                            message=f"Service '{svc.name}' image '{image}' is unpinned or uses ':latest'.",
                            suggested_fix=f"Pin '{image}' to a specific version tag (e.g., {image.split(':')[0]}:<version>).",
                        )
                    )

        return findings
