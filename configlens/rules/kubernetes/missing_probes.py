"""Rule detecting containers missing liveness and readiness probes in Kubernetes manifests."""

from pathlib import Path
from typing import List, Set
from configlens.models import Category, Finding, Severity
from configlens.parsers.k8s_models import K8sManifestFile
from configlens.rules.base import Rule, parse_inline_suppressions

# Long-running service workloads where health probes are essential
LONG_RUNNING_WORKLOADS: Set[str] = {
    "Deployment",
    "StatefulSet",
    "DaemonSet",
    "Pod",
}


class K8sMissingProbesRule(Rule):
    """Flags service containers that lack liveness or readiness probes."""

    id = "k8s-missing-probes"
    title = "Missing health probes on service container"
    description = (
        "Long-running service containers should define liveness and readiness probes "
        "for automated health monitoring, traffic routing, and restart recovery."
    )
    severity = Severity.MEDIUM
    category = Category.KUBERNETES

    def check(self, file_path: Path, parsed: K8sManifestFile) -> List[Finding]:
        """Inspect service workloads for configured health probes."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for container in parsed.containers:
            if container.document_kind not in LONG_RUNNING_WORKLOADS:
                continue

            has_liveness = container.liveness_probe is not None
            has_readiness = container.readiness_probe is not None

            if not (has_liveness or has_readiness):
                if not self.is_line_suppressed(suppressions, container.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=container.line_number,
                            message=(
                                f"Container '{container.name}' in {container.document_kind} "
                                f"'{container.document_name}' lacks liveness and readiness probes."
                            ),
                            suggested_fix=(
                                f"Define 'livenessProbe' and 'readinessProbe' for container "
                                f"'{container.name}'."
                            ),
                        )
                    )

        return findings
