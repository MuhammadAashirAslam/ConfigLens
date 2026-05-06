"""Parser for Docker Compose configuration files with line-number tracking."""

from pathlib import Path
from typing import Any, Dict, Optional
from configlens.parsers.compose_models import ComposeFile, ComposeService
from configlens.parsers.yaml_loader import AnnotatedDict, load_yaml_with_line_numbers


def parse_compose_content(content: str, path: Optional[Path] = None) -> ComposeFile:
    """Parse Docker Compose YAML content into typed ComposeFile with line numbers."""
    target_path = path or Path("docker-compose.yml")
    parsed_data = load_yaml_with_line_numbers(content)

    if not isinstance(parsed_data, dict):
        return ComposeFile(path=target_path, line_number=1, raw={})

    comp_line = getattr(parsed_data, "line_number", 1)
    version = parsed_data.get("version")
    services_dict: Dict[str, ComposeService] = {}

    raw_services = parsed_data.get("services")
    if isinstance(raw_services, dict):
        for svc_name, svc_data in raw_services.items():
            if not isinstance(svc_data, dict):
                continue

            if isinstance(raw_services, AnnotatedDict):
                svc_line = raw_services.get_line(str(svc_name), getattr(svc_data, "line_number", comp_line))
            else:
                svc_line = getattr(svc_data, "line_number", comp_line)

            ports_raw = svc_data.get("ports")
            ports_list = ports_raw if isinstance(ports_raw, list) else []

            volumes_raw = svc_data.get("volumes")
            volumes_list = volumes_raw if isinstance(volumes_raw, list) else []

            service = ComposeService(
                name=str(svc_name),
                line_number=svc_line,
                image=svc_data.get("image"),
                build=svc_data.get("build"),
                ports=ports_list,
                environment=svc_data.get("environment", {}),
                restart=svc_data.get("restart"),
                volumes=volumes_list,
                raw=dict(svc_data),
            )
            services_dict[str(svc_name)] = service

    networks = parsed_data.get("networks", {})
    volumes = parsed_data.get("volumes", {})

    return ComposeFile(
        path=target_path,
        line_number=comp_line,
        version=str(version) if version is not None else None,
        services=services_dict,
        networks=dict(networks) if isinstance(networks, dict) else {},
        volumes=dict(volumes) if isinstance(volumes, dict) else {},
        raw=dict(parsed_data),
    )


def parse_compose_file(path: Path) -> ComposeFile:
    """Read and parse a Docker Compose file from disk."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return ComposeFile(path=path, line_number=1, raw={})
    return parse_compose_content(content, path=path)
