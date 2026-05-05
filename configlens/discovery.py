"""DevOps configuration file discovery and category classification."""

import os
from pathlib import Path
from configlens.models import Category


def is_github_actions_workflow(path: Path) -> bool:
    """Check if the given path is a GitHub Actions workflow file.

    Pattern: .github/workflows/*.{yml,yaml}
    """
    norm = path.as_posix()
    if "/.github/workflows/" in norm or norm.startswith(".github/workflows/"):
        return path.suffix.lower() in {".yml", ".yaml"}
    return False


def is_dockerfile(path: Path) -> bool:
    """Check if the given path is a Dockerfile by name or content inspection.

    Patterns: Dockerfile*, *.dockerfile, Containerfile*
    """
    name = path.name.lower()
    if name.startswith("dockerfile") or name.endswith(".dockerfile") or name.startswith("containerfile"):
        return True

    # Content heuristic if small file and extensionless or unknown
    if path.is_file() and not path.suffix and path.stat().st_size < 100_000:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    first_token = stripped.split()[0].upper()
                    if first_token in {"FROM", "ARG", "LABEL"}:
                        return True
                    break
        except (OSError, PermissionError):
            pass

    return False


def is_docker_compose(path: Path) -> bool:
    """Check if the given path is a Docker Compose file.

    Patterns: compose*.{yml,yaml}, docker-compose*.{yml,yaml}
    """
    name = path.name.lower()
    if path.suffix.lower() not in {".yml", ".yaml"}:
        return False

    if name.startswith("docker-compose") or name.startswith("compose"):
        return True

    # Check top-level services: key for other YAML files
    if path.is_file() and path.stat().st_size < 200_000:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("services:"):
                        return True
        except (OSError, PermissionError):
            pass

    return False
