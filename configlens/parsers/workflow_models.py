"""Typed intermediate representation (IR) for GitHub Actions workflows."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStep:
    """Represents a single step in a GitHub Actions workflow job."""

    line_number: int
    name: Optional[str] = None
    step_id: Optional[str] = None
    uses: Optional[str] = None
    run: Optional[str] = None
    with_args: Dict[str, Any] = field(default_factory=dict)
    env: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowJob:
    """Represents a job in a GitHub Actions workflow."""

    job_id: str
    line_number: int
    name: Optional[str] = None
    runs_on: Optional[Any] = None
    timeout_minutes: Optional[int] = None
    permissions: Optional[Any] = None
    steps: List[WorkflowStep] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowFile:
    """Represents a parsed GitHub Actions workflow file."""

    path: Path
    line_number: int = 1
    name: Optional[str] = None
    on: Optional[Any] = None
    permissions: Optional[Any] = None
    jobs: Dict[str, WorkflowJob] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_steps(self) -> List[WorkflowStep]:
        """Convenience property to access all steps across all jobs."""
        steps: List[WorkflowStep] = []
        for job in self.jobs.values():
            steps.extend(job.steps)
        return steps
