"""Unit tests for Docker Compose and Dockerfile parsers."""

from pathlib import Path
from configlens.parsers.compose_parser import parse_compose_content, parse_compose_file
from configlens.parsers.dockerfile_parser import parse_dockerfile_content, parse_dockerfile_file

SAMPLE_COMPOSE_YAML = """version: "3.8"

services:
  web:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
    environment:
      ENV: production

  db:
    image: postgres:15
    restart: on-failure
    ports:
      - "5432:5432"
"""

SAMPLE_DOCKERFILE = """# Base stage
FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update && \\
    apt-get install -y gcc && \\
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-alpine
WORKDIR /app
COPY --from=builder /app /app
USER 10001
CMD ["python", "main.py"]
"""


def test_parse_compose_services():
    """Verify Docker Compose parser extracts services and line numbers."""
    compose = parse_compose_content(SAMPLE_COMPOSE_YAML)

    assert compose.version == "3.8"
    assert len(compose.services) == 2

    # Check web service
    web = compose.services["web"]
    assert web.name == "web"
    assert web.image == "nginx:alpine"
    assert web.restart == "always"
    assert web.ports == ["80:80"]
    assert web.line_number == 4

    # Check db service
    db = compose.services["db"]
    assert db.name == "db"
    assert db.image == "postgres:15"
    assert db.restart == "on-failure"
    assert db.ports == ["5432:5432"]
    assert db.line_number == 12


def test_parse_compose_malformed():
    """Verify malformed compose file does not raise exception."""
    compose = parse_compose_content("services: [malformed")
    assert compose.line_number >= 1
    assert len(compose.services) == 0


def test_parse_compose_file_missing():
    """Verify missing compose file degrades gracefully."""
    compose = parse_compose_file(Path("non_existent_compose.yml"))
    assert compose.line_number == 1
    assert len(compose.services) == 0


def test_parse_dockerfile_multi_stage():
    """Verify Dockerfile parser handles multi-stage builds and line continuations."""
    df = parse_dockerfile_content(SAMPLE_DOCKERFILE)

    assert len(df.stages) == 2
    assert len(df.parse_errors) == 0

    # Stage 0 (builder)
    stage0 = df.stages[0]
    assert stage0.index == 0
    assert stage0.base_image == "python:3.11-slim"
    assert stage0.name == "builder"
    assert stage0.line_number == 2

    # Stage 1 (final)
    stage1 = df.stages[1]
    assert stage1.index == 1
    assert stage1.base_image == "python:3.11-alpine"
    assert stage1.name is None
    assert stage1.line_number == 13

    # Check line continuation instruction
    run_inst = [inst for inst in df.instructions if inst.instruction == "RUN"][0]
    assert run_inst.line_number == 5
    assert "apt-get update && apt-get install -y gcc" in run_inst.arguments

    # Check USER instruction
    user_inst = df.find_instructions("USER")[0]
    assert user_inst.arguments == "10001"
    assert user_inst.line_number == 16


def test_parse_dockerfile_empty_and_comments():
    """Verify Dockerfile parser handles empty and comments-only content."""
    df = parse_dockerfile_content("# Just a comment\n\n# Another comment\n")
    assert len(df.instructions) == 0
    assert len(df.stages) == 0
    assert len(df.parse_errors) == 0


def test_parse_dockerfile_file_missing():
    """Verify missing Dockerfile degrades gracefully."""
    df = parse_dockerfile_file(Path("non_existent_Dockerfile"))
    assert len(df.parse_errors) == 1
