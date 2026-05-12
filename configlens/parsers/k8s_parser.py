"""Parser for Kubernetes YAML manifests with line number tracking."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from configlens.parsers.k8s_models import K8sContainer, K8sDocument, K8sManifestFile
from configlens.parsers.yaml_loader import AnnotatedDict, AnnotatedList, load_all_yaml_with_line_numbers


def parse_k8s_content(content: str, path: Optional[Path] = None) -> K8sManifestFile:
    """Parse raw YAML manifest content into a typed K8sManifestFile."""
    target_path = path or Path("manifest.yaml")
    docs_raw = load_all_yaml_with_line_numbers(content)

    documents: List[K8sDocument] = []
    parse_errors: List[str] = []

    for raw in docs_raw:
        if not isinstance(raw, dict):
            continue

        if "__parse_error__" in raw:
            parse_errors.append(str(raw["__parse_error__"]))
            continue

        api_version = str(raw.get("apiVersion", raw.get("api_version", "")))
        kind = str(raw.get("kind", ""))
        metadata = raw.get("metadata", {}) if isinstance(raw.get("metadata"), dict) else {}
        name = str(metadata.get("name", "unnamed"))
        namespace = str(metadata.get("namespace")) if metadata.get("namespace") else None
        doc_line = getattr(raw, "line_number", 1)

        # Locate pod spec based on workload kind
        pod_spec: Dict[str, Any] = {}
        spec = raw.get("spec", {})
        if isinstance(spec, dict):
            if kind == "Pod":
                pod_spec = spec
            elif kind in {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job"}:
                template = spec.get("template", {})
                if isinstance(template, dict):
                    pod_spec = template.get("spec", {}) if isinstance(template.get("spec"), dict) else {}
            elif kind == "CronJob":
                job_tmpl = spec.get("jobTemplate", {})
                if isinstance(job_tmpl, dict):
                    tmpl_spec = job_tmpl.get("spec", {})
                    if isinstance(tmpl_spec, dict):
                        template = tmpl_spec.get("template", {})
                        if isinstance(template, dict):
                            pod_spec = template.get("spec", {}) if isinstance(template.get("spec"), dict) else {}

        pod_sec_context: Dict[str, Any] = {}
        if isinstance(pod_spec, dict):
            raw_sec = pod_spec.get("securityContext", {})
            if isinstance(raw_sec, dict):
                pod_sec_context = dict(raw_sec)

        # Extract containers
        containers: List[K8sContainer] = []
        raw_containers: List[Any] = []
        if isinstance(pod_spec, dict):
            c_list = pod_spec.get("containers", [])
            if isinstance(c_list, list):
                raw_containers.extend(c_list)
            init_c_list = pod_spec.get("initContainers", [])
            if isinstance(init_c_list, list):
                raw_containers.extend(init_c_list)

        for c in raw_containers:
            if not isinstance(c, dict):
                continue
            c_name = str(c.get("name", "unnamed"))
            c_image = str(c.get("image", ""))
            c_line = getattr(c, "line_number", doc_line)
            c_res = dict(c.get("resources", {})) if isinstance(c.get("resources"), dict) else {}
            c_sec = dict(c.get("securityContext", {})) if isinstance(c.get("securityContext"), dict) else {}
            l_probe = c.get("livenessProbe") if isinstance(c.get("livenessProbe"), dict) else None
            r_probe = c.get("readinessProbe") if isinstance(c.get("readinessProbe"), dict) else None
            s_probe = c.get("startupProbe") if isinstance(c.get("startupProbe"), dict) else None

            containers.append(
                K8sContainer(
                    name=c_name,
                    image=c_image,
                    line_number=c_line,
                    resources=c_res,
                    security_context=c_sec,
                    liveness_probe=l_probe,
                    readiness_probe=r_probe,
                    startup_probe=s_probe,
                    pod_security_context=pod_sec_context,
                    document_kind=kind,
                    document_name=name,
                )
            )

        documents.append(
            K8sDocument(
                api_version=api_version,
                kind=kind,
                name=name,
                namespace=namespace,
                line_number=doc_line,
                pod_security_context=pod_sec_context,
                containers=containers,
                raw_data=raw,
            )
        )

    return K8sManifestFile(path=target_path, documents=documents, parse_errors=parse_errors)


def parse_k8s_file(path: Path) -> K8sManifestFile:
    """Read and parse a Kubernetes YAML manifest file from disk."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError) as err:
        return K8sManifestFile(path=path, parse_errors=[str(err)])
    return parse_k8s_content(content, path=path)
