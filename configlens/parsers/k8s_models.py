"""Typed intermediate representation (IR) models for Kubernetes manifests."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class K8sContainer:
    """Represents a container specification within a Kubernetes pod or workload."""

    name: str
    image: str
    line_number: int
    resources: Dict[str, Any] = field(default_factory=dict)
    security_context: Dict[str, Any] = field(default_factory=dict)
    liveness_probe: Optional[Dict[str, Any]] = None
    readiness_probe: Optional[Dict[str, Any]] = None
    startup_probe: Optional[Dict[str, Any]] = None
    pod_security_context: Dict[str, Any] = field(default_factory=dict)
    document_kind: str = ""
    document_name: str = ""


@dataclass
class K8sDocument:
    """Represents a single Kubernetes YAML document in a manifest file."""

    api_version: str
    kind: str
    name: str
    line_number: int
    namespace: Optional[str] = None
    pod_security_context: Dict[str, Any] = field(default_factory=dict)
    containers: List[K8sContainer] = field(default_factory=list)
    raw_data: Any = None


@dataclass
class K8sManifestFile:
    """Represents a parsed Kubernetes manifest file with one or more YAML documents."""

    path: Path
    documents: List[K8sDocument] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)

    @property
    def containers(self) -> List[K8sContainer]:
        """Convenience property yielding all containers across all documents."""
        all_c: List[K8sContainer] = []
        for doc in self.documents:
            all_c.extend(doc.containers)
        return all_c
