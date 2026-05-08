"""Rule detecting package manager caches left in Dockerfile RUN layers."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.dockerfile_models import DockerfileParsed
from configlens.rules.base import Rule, parse_inline_suppressions

APT_INSTALL = re.compile(r"\bapt(?:-get)?\s+install\b")
APT_CLEAN = re.compile(r"rm\s+-rf\s+/var/lib/apt/lists/\*")
PIP_INSTALL = re.compile(r"\bpip\s+install\b")
PIP_NO_CACHE = re.compile(r"--no-cache-dir")


class UncachedPkgManagerRule(Rule):
    """Flags Dockerfile RUN instructions that install packages without clearing package caches."""

    id = "dockerfile-uncached-pkg-manager"
    title = "Package manager cache not cleaned"
    description = "Package managers leave downloaded indexes and tarballs in the image layer unless cleaned in the same RUN instruction."
    severity = Severity.MEDIUM
    category = Category.DOCKERFILE

    def check(self, file_path: Path, parsed: DockerfileParsed) -> List[Finding]:
        """Inspect RUN instructions for package installations lacking cleanup."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for inst in parsed.find_instructions("RUN"):
            cmd = inst.arguments

            # Check apt
            if APT_INSTALL.search(cmd) and not APT_CLEAN.search(cmd):
                if not self.is_line_suppressed(suppressions, inst.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=inst.line_number,
                            message="apt-get install runs without clearing lists cache with 'rm -rf /var/lib/apt/lists/*'.",
                            suggested_fix="Append '&& rm -rf /var/lib/apt/lists/*' to the apt-get install instruction.",
                        )
                    )

            # Check pip
            if PIP_INSTALL.search(cmd) and not PIP_NO_CACHE.search(cmd):
                if not self.is_line_suppressed(suppressions, inst.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=inst.line_number,
                            message="pip install runs without the '--no-cache-dir' flag.",
                            suggested_fix="Add '--no-cache-dir' to pip install to avoid bloating image layers with wheels.",
                        )
                    )

        return findings
