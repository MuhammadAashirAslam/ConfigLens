"""Rule detecting containers running in privileged mode in Kubernetes manifests."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.k8s_models import K8sManifestFile
from configlens.rules.base import Rule, parse_inline_suppressions


class K8sPrivilegedContainerRule(Rule):
    """Flags containers running with securityContext.privileged set to true."""

    id = "k8s-privileged-container"
    title = "Privileged container mode enabled"
    description = (
        "Running containers in privileged mode disables all Linux security protections "
        "and grants the container root capabilities equivalent to the host."
    )
    severity = Severity.CRITICAL
    category = Category.KUBERNETES

    def check(self, file_path: Path, parsed: K8sManifestFile) -> List[Finding]:
        """Inspect container security contexts for privileged execution."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for container in parsed.containers:
            sec_ctx = container.security_context
            if isinstance(sec_ctx, dict) and sec_ctx.get("privileged") is True:
                if not self.is_line_suppressed(suppressions, container.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=container.line_number,
                            message=(
                                f"Container '{container.name}' in {container.document_kind} "
                                f"'{container.document_name}' runs in privileged mode."
                            ),
                            suggested_fix=(
                                f"Remove 'privileged: true' from container '{container.name}' "
                                "and use specific Linux capabilities via securityContext.capabilities.add."
                            ),
                        )
                    )

        return findings
