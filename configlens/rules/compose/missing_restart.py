"""Rule detecting missing or disabled restart policies in Docker Compose services."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.compose_models import ComposeFile
from configlens.rules.base import Rule, parse_inline_suppressions


class ComposeMissingRestartRule(Rule):
    """Flags Docker Compose services lacking an automatic restart policy."""

    id = "compose-missing-restart"
    title = "Missing service restart policy"
    description = "Production services should declare a restart policy (e.g. unless-stopped or always) to ensure automatic recovery upon crash or host reboot."
    severity = Severity.MEDIUM
    category = Category.DOCKER_COMPOSE

    def check(self, file_path: Path, parsed: ComposeFile) -> List[Finding]:
        """Check all services for missing restart policy."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for svc in parsed.services.values():
            restart = svc.restart
            if restart is None or str(restart).lower() in {"no", "false"}:
                if not self.is_line_suppressed(suppressions, svc.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=svc.line_number,
                            message=f"Service '{svc.name}' has no restart policy configured.",
                            suggested_fix=f"Add 'restart: unless-stopped' or 'restart: always' to service '{svc.name}'.",
                        )
                    )

        return findings
