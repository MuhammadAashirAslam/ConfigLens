"""Typed intermediate representation (IR) models for Dockerfiles."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class DockerfileInstruction:
    """Represents a single instruction inside a Dockerfile."""

    instruction: str
    arguments: str
    line_number: int
    raw_line: str
    stage_index: int = 0


@dataclass
class DockerfileStage:
    """Represents a build stage in a multi-stage Dockerfile."""

    index: int
    base_image: str
    line_number: int
    name: Optional[str] = None
    instructions: List[DockerfileInstruction] = field(default_factory=list)


@dataclass
class DockerfileParsed:
    """Represents a parsed Dockerfile with instructions and stage breakdowns."""

    path: Path
    instructions: List[DockerfileInstruction] = field(default_factory=list)
    stages: List[DockerfileStage] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)

    def find_instructions(self, name: str) -> List[DockerfileInstruction]:
        """Find all instructions of a specific type (case-insensitive)."""
        upper = name.upper()
        return [inst for inst in self.instructions if inst.instruction.upper() == upper]
