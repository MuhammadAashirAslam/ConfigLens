"""Rule detecting containers running as root or without non-root securityContext in Kubernetes."""

from pathlib import Path
from typing import Any, Dict, List
from configlens.models import Category, Finding, Severity
from configlens.parsers.k8s_models import K8sManifestFile
from configlens.rules.base import Rule, parse_inline_suppressions


def _is_non_root(sec_ctx: Dict[str, Any]) -> bool:
    """Check if a securityContext enforces non-root execution."""
    if not sec_ctx or not isinstance(sec_ctx, dict):
        return False
    if sec_ctx.get("runAsNonRoot") is True:
        return True
    user = sec_ctx.get("runAsUser")
    if user is not None:
        try:
            return int(user) > 0
        except (ValueError, TypeError):
            pass
    return False


class K8sRootContainerRule(Rule):
    """Flags containers configured to run as root or lacking non-root security context."""

    id = "k8s-root-container"
    title = "Container may run as root user"
    description = (
        "Containers should run with non-root privileges by configuring "
        "'securityContext.runAsNonRoot: true' or a non-zero 'runAsUser'."
    )
    severity = Severity.CRITICAL
    category = Category.KUBERNETES

    def check(self, file_path: Path, parsed: K8sManifestFile) -> List[Finding]:
        """Inspect container and pod security contexts for non-root enforcement."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for container in parsed.containers:
            # Container-level explicitly set to root overrides pod-level
            c_sec = container.security_context
            p_sec = container.pod_security_context

            c_user = c_sec.get("runAsUser") if isinstance(c_sec, dict) else None
            c_non_root = c_sec.get("runAsNonRoot") if isinstance(c_sec, dict) else None

            # Explicit root override
            is_explicit_root = (c_user == 0) or (c_non_root is False)

            if is_explicit_root or not (_is_non_root(c_sec) or _is_non_root(p_sec)):
                if not self.is_line_suppressed(suppressions, container.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=container.line_number,
                            message=(
                                f"Container '{container.name}' in {container.document_kind} "
                                f"'{container.document_name}' lacks non-root securityContext enforcement."
                            ),
                            suggested_fix=(
                                "Set 'securityContext.runAsNonRoot: true' or a non-zero 'runAsUser' "
                                f"for container '{container.name}'."
                            ),
                        )
                    )

        return findings
