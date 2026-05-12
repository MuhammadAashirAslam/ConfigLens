"""Rule detecting containers missing CPU and memory resource limits in Kubernetes manifests."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.k8s_models import K8sManifestFile
from configlens.rules.base import Rule, parse_inline_suppressions


class K8sMissingResourceLimitsRule(Rule):
    """Flags containers without configured CPU or memory resource limits."""

    id = "k8s-missing-resource-limits"
    title = "Missing container resource limits"
    description = (
        "Containers should specify CPU and memory resource limits to avoid cluster "
        "node exhaustion, noisy neighbor issues, and unexpected OOM kills."
    )
    severity = Severity.HIGH
    category = Category.KUBERNETES

    def check(self, file_path: Path, parsed: K8sManifestFile) -> List[Finding]:
        """Inspect all containers across documents for resource limits."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for container in parsed.containers:
            limits = container.resources.get("limits", {})
            has_cpu_limit = bool(limits and limits.get("cpu"))
            has_mem_limit = bool(limits and limits.get("memory"))

            if not (has_cpu_limit and has_mem_limit):
                if not self.is_line_suppressed(suppressions, container.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=container.line_number,
                            message=(
                                f"Container '{container.name}' in {container.document_kind} "
                                f"'{container.document_name}' is missing CPU and/or memory resource limits."
                            ),
                            suggested_fix=(
                                f"Specify 'resources.limits.cpu' and 'resources.limits.memory' "
                                f"for container '{container.name}'."
                            ),
                        )
                    )

        return findings
