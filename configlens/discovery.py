"""DevOps configuration file discovery and category classification."""

import fnmatch
import os
from pathlib import Path
from typing import List, Optional, Set
from configlens.models import Category, DiscoveredFile

# Common directories always ignored during scans
DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".tox",
    ".idea",
    ".vscode",
}


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

    Patterns: Dockerfile, Dockerfile.*, *.dockerfile, Containerfile, Containerfile.*
    """
    # Exclude common non-container extensions
    if path.suffix.lower() in {
        ".py", ".sh", ".md", ".json", ".txt", ".yaml", ".yml",
        ".tf", ".tfvars", ".toml", ".xml", ".html", ".js", ".ts",
    }:
        return False

    name = path.name.lower()
    if (
        name == "dockerfile"
        or name.startswith("dockerfile.")
        or name.endswith(".dockerfile")
        or name == "containerfile"
        or name.startswith("containerfile.")
    ):
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


def is_terraform(path: Path) -> bool:
    """Check if the given path is a Terraform configuration file.

    Patterns: *.tf, *.tfvars
    """
    suffix = path.suffix.lower()
    return suffix in {".tf", ".tfvars"}


def is_kubernetes(path: Path) -> bool:
    """Check if the given path is a Kubernetes manifest.

    Patterns: YAML file containing apiVersion and kind keys, or located in k8s/ dirs.
    """
    if path.suffix.lower() not in {".yml", ".yaml"}:
        return False

    # Skip GitHub Actions and Compose
    if is_github_actions_workflow(path) or is_docker_compose(path):
        return False

    norm = path.as_posix().lower()
    in_k8s_dir = any(k in norm for k in ["/k8s/", "/kubernetes/", "/manifests/", "/helm/"])

    if path.is_file() and path.stat().st_size < 500_000:
        try:
            has_api_version = False
            has_kind = False
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("apiVersion:"):
                        has_api_version = True
                    elif stripped.startswith("kind:"):
                        has_kind = True
                    if has_api_version and has_kind:
                        return True
            if in_k8s_dir and (has_api_version or has_kind):
                return True
        except (OSError, PermissionError):
            pass

    return False


def detect_category(path: Path) -> Category:
    """Detect the DevOps category of a given file path."""
    if is_github_actions_workflow(path):
        return Category.GITHUB_ACTIONS
    if is_dockerfile(path):
        return Category.DOCKERFILE
    if is_docker_compose(path):
        return Category.DOCKER_COMPOSE
    if is_terraform(path):
        return Category.TERRAFORM
    if is_kubernetes(path):
        return Category.KUBERNETES
    return Category.UNKNOWN


def parse_ignore_file(ignore_path: Path) -> List[str]:
    """Parse ignore patterns from a gitignore or configlensignore file."""
    patterns: List[str] = []
    if not ignore_path.is_file():
        return patterns

    try:
        with open(ignore_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    except (OSError, PermissionError):
        pass
    return patterns


def should_ignore_path(rel_path: Path, patterns: List[str]) -> bool:
    """Check if a relative path matches any ignore patterns."""
    rel_str = rel_path.as_posix()
    name = rel_path.name

    for pattern in patterns:
        clean_pat = pattern.rstrip("/")
        # Exact match or glob match against basename
        if fnmatch.fnmatch(name, clean_pat):
            return True
        # Match against full relative path
        if fnmatch.fnmatch(rel_str, clean_pat) or fnmatch.fnmatch(rel_str, f"*/{clean_pat}"):
            return True
        if pattern.endswith("/") and fnmatch.fnmatch(f"{rel_str}/", f"*{clean_pat}/*"):
            return True
    return False


def discover_files(
    root: Path,
    respect_gitignore: bool = True,
    only: Optional[Set[Category]] = None,
    ignore_file: Optional[Path] = None,
) -> List[DiscoveredFile]:
    """Recursively scan root directory and return classified DevOps configuration files."""
    root = root.resolve()
    if not root.exists():
        return []

    if root.is_file():
        category = detect_category(root)
        if category != Category.UNKNOWN and (only is None or category in only):
            return [
                DiscoveredFile(
                    path=root,
                    category=category,
                    relative_path=Path(root.name),
                    size_bytes=root.stat().st_size,
                )
            ]
        return []

    # Load ignore patterns
    ignore_patterns: List[str] = []
    if respect_gitignore:
        ignore_patterns.extend(parse_ignore_file(root / ".gitignore"))
    if ignore_file and ignore_file.is_file():
        ignore_patterns.extend(parse_ignore_file(ignore_file))
    elif (root / ".configlensignore").is_file():
        ignore_patterns.extend(parse_ignore_file(root / ".configlensignore"))

    discovered: List[DiscoveredFile] = []

    for dirpath_str, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath_str)
        rel_dir = dirpath.relative_to(root)

        # Prune ignored directories
        dirnames[:] = [
            d
            for d in dirnames
            if d not in DEFAULT_IGNORED_DIRS
            and not should_ignore_path(rel_dir / d, ignore_patterns)
        ]

        # Check for nested .gitignore
        if respect_gitignore and (dirpath / ".gitignore").is_file():
            ignore_patterns.extend(parse_ignore_file(dirpath / ".gitignore"))

        for filename in filenames:
            file_path = dirpath / filename
            rel_file = file_path.relative_to(root)

            if should_ignore_path(rel_file, ignore_patterns):
                continue

            category = detect_category(file_path)
            if category == Category.UNKNOWN:
                continue

            if only is not None and category not in only:
                continue

            try:
                size = file_path.stat().st_size
            except (OSError, PermissionError):
                size = 0

            discovered.append(
                DiscoveredFile(
                    path=file_path,
                    category=category,
                    relative_path=rel_file,
                    size_bytes=size,
                )
            )

    discovered.sort(key=lambda f: f.relative_path.as_posix())
    return discovered
