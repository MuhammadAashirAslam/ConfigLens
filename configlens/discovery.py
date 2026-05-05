"""DevOps configuration file discovery and category classification."""

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
