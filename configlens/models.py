"""Core domain models for ConfigLens."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict


class Category(str, Enum):
    """Supported DevOps configuration categories."""

    GITHUB_ACTIONS = "github-actions"
    DOCKERFILE = "dockerfile"
    DOCKER_COMPOSE = "docker-compose"
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    UNKNOWN = "unknown"

    @property
    def display_name(self) -> str:
        """Human-readable display name for terminal and reports."""
        names = {
            Category.GITHUB_ACTIONS: "GitHub Actions",
            Category.DOCKERFILE: "Dockerfile",
            Category.DOCKER_COMPOSE: "Docker Compose",
            Category.TERRAFORM: "Terraform",
            Category.KUBERNETES: "Kubernetes",
            Category.UNKNOWN: "Unknown",
        }
        return names.get(self, self.value)


@dataclass(frozen=True)
class DiscoveredFile:
    """Represents a discovered DevOps configuration file in a repository."""

    path: Path
    category: Category
    relative_path: Path
    size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert discovered file info to a dictionary."""
        return {
            "path": str(self.path),
            "relative_path": str(self.relative_path),
            "category": self.category.value,
            "size_bytes": self.size_bytes,
        }
