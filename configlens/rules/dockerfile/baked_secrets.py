"""Rule detecting secrets or sensitive tokens hardcoded in Dockerfile ENV or ARG."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions

SENSITIVE_KEY_PATTERN = re.compile(
    r"\b(password|secret|token|api[_-]?key|private[_-]?key|access[_-]?token|credentials?)\b",
    re.IGNORECASE,
)
SAFE_PLACEHOLDERS = {"", "placeholder", "dummy", "example", "changeme", "none", "null"}


class DockerfileBakedSecretsRule(Rule):
    """Flags Dockerfiles baking sensitive tokens or passwords into ENV or ARG instructions."""

    id = "dockerfile-baked-secrets"
    title = "Secrets or credentials baked into image layers"
    description = "Secrets assigned in ENV or ARG persist in image metadata and intermediate layers, exposing credentials to anyone with image pull access."
    severity = Severity.CRITICAL
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Check all ENV and ARG instructions for embedded credentials."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for inst in parsed.instructions:
            if inst.instruction not in {"ENV", "ARG"}:
                continue

            args = inst.arguments.strip()
            # Parse KEY=VAL or KEY VAL
            pairs = []
            if "=" in args:
                # Handle multiple KEY=VAL pairs
                for match in re.finditer(r"([A-Za-z0-9_-]+)=([^\s]+)", args):
                    pairs.append((match.group(1), match.group(2).strip("\"'")))
            else:
                tokens = args.split(maxsplit=1)
                if len(tokens) == 2:
                    pairs.append((tokens[0], tokens[1].strip("\"'")))

            for key, val in pairs:
                if SENSITIVE_KEY_PATTERN.search(key):
                    if val.lower() not in SAFE_PLACEHOLDERS and len(val) >= 4:
                        if not self.is_line_suppressed(suppressions, inst.line_number):
                            findings.append(
                                self.create_finding(
                                    file_path=file_path,
                                    line_number=inst.line_number,
                                    message=f"Hardcoded sensitive value assigned to '{key}' in {inst.instruction} instruction.",
                                    suggested_fix="Inject credentials at build time with BuildKit secret mounts ('--mount=type=secret') or pass at runtime.",
                                )
                            )

        return findings
