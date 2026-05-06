"""Typed intermediate representation (IR) for Docker Compose files."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ComposeService:
    """Represents a single service definition in Docker Compose."""

    name: str
    line_number: int
    image: Optional[str] = None
    build: Optional[Any] = None
    ports: List[Any] = field(default_factory=list)
    environment: Any = field(default_factory=dict)
    restart: Optional[str] = None
    volumes: List[Any] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComposeFile:
    """Represents a parsed Docker Compose file."""

    path: Path
    line_number: int = 1
    version: Optional[str] = None
    services: Dict[str, ComposeService] = field(default_factory=dict)
    networks: Dict[str, Any] = field(default_factory=dict)
    volumes: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
