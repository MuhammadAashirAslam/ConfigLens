"""Rule detecting hardcoded credentials in Docker Compose service environment definitions."""

import re
from pathlib import Path
from typing import List, Tuple
from configlens.models import Category, Finding, Severity
from configlens.parsers.compose_models import ComposeFile
from configlens.rules.base import Rule, parse_inline_suppressions

SENSITIVE_KEY_PATTERN = re.compile(
    r"\b(password|secret|token|api[_-]?key|private[_-]?key|auth)\b",
    re.IGNORECASE,
)
SAFE_VALUES = {"", "placeholder", "dummy", "example", "changeme", "none", "null"}


class ComposeHardcodedCredentialsRule(Rule):
    """Flags plaintext passwords or secrets in Docker Compose environment declarations."""

    id = "compose-hardcoded-credentials"
    title = "Hardcoded credentials in environment variables"
    description = "Service environment variables should not contain plaintext passwords or tokens. Use .env files or Docker secrets."
    severity = Severity.CRITICAL
    category = Category.DOCKER_COMPOSE

    def check(self, file_path: Path, parsed: ComposeFile) -> List[Finding]:
        """Inspect environment blocks of all compose services."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for svc in parsed.services.values():
            env_pairs: List[Tuple[str, str]] = []

            # Handle dict format: {KEY: val}
            if isinstance(svc.environment, dict):
                for k, v in svc.environment.items():
                    env_pairs.append((str(k), str(v) if v is not None else ""))
            # Handle list format: ["KEY=val", ...]
            elif isinstance(svc.environment, list):
                for item in svc.environment:
                    if isinstance(item, str) and "=" in item:
                        k, v = item.split("=", 1)
                        env_pairs.append((k.strip(), v.strip()))

            for key, val in env_pairs:
                if SENSITIVE_KEY_PATTERN.search(key):
                    # Check if val is a template variable like ${DB_PASSWORD} or dummy
                    if not val.startswith("${") and val.lower() not in SAFE_VALUES and len(val) >= 4:
                        if not self.is_line_suppressed(suppressions, svc.line_number):
                            findings.append(
                                self.create_finding(
                                    file_path=file_path,
                                    line_number=svc.line_number,
                                    message=f"Service '{svc.name}' contains hardcoded sensitive credential in '{key}'.",
                                    suggested_fix=f"Extract credential to a .env file and reference with '${{{key}}}'.",
                                )
                            )

        return findings
