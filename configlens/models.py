"""Core domain models for ConfigLens."""

from enum import Enum


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
