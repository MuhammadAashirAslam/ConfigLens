"""Rule detecting containers using latest or unpinned image tags in Kubernetes."""

from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.k8s_models import K8sManifestFile
from configlens.rules.base import Rule, parse_inline_suppressions


class K8sLatestImageTagRule(Rule):
    """Flags container images that use the :latest tag or omit a version tag."""

    id = "k8s-latest-image-tag"
    title = "Container image uses latest or untagged version"
    description = (
        "Container images should be pinned to an immutable semantic version or image digest "
        "to guarantee deterministic deployments and reproducible rollouts."
    )
    severity = Severity.HIGH
    category = Category.KUBERNETES

    def check(self, file_path: Path, parsed: K8sManifestFile) -> List[Finding]:
        """Inspect all container image references for unpinned or latest tags."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for container in parsed.containers:
            image = container.image.strip()
            if not image:
                continue

            # Check if image is pinned by sha256 digest
            is_digest = "@sha256:" in image

            # Check for untagged or latest
            # E.g.: "nginx", "redis:latest", "gcr.io/proj/app"
            is_unpinned = False
            if not is_digest:
                # Discard registry host/port prefix before checking tag
                image_path = image.split("/", 1)[1] if "/" in image and ":" in image.split("/")[0] else image
                if ":" not in image_path:
                    is_unpinned = True
                elif image.endswith(":latest"):
                    is_unpinned = True

            if is_unpinned:
                if not self.is_line_suppressed(suppressions, container.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=container.line_number,
                            message=(
                                f"Container '{container.name}' in {container.document_kind} "
                                f"'{container.document_name}' uses unpinned or latest image '{image}'."
                            ),
                            suggested_fix=(
                                f"Pin container image '{image}' to a specific version tag or immutable SHA digest."
                            ),
                        )
                    )

        return findings
