"""Core domain models for ConfigLens."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


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


class Severity(str, Enum):
    """Severity levels for configuration debt and risk findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        """Numeric rank for severity threshold comparisons."""
        ranks = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
        }
        return ranks[self]


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


@dataclass(frozen=True)
class Finding:
    """Represents a configuration debt or risk finding discovered by a rule."""

    rule_id: str
    title: str
    severity: Severity
    category: Category
    file_path: Path
    line_number: int
    message: str
    suggested_fix: str
    column: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to a JSON-serializable dictionary."""
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.value,
            "category": self.category.value,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "column": self.column,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
        }
