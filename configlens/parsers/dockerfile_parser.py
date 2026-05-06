"""Lightweight Dockerfile parser handling multi-stage builds and line continuations."""

import re
from pathlib import Path
from typing import List, Optional
from configlens.parsers.dockerfile_models import (
    DockerfileInstruction,
    DockerfileParsed,
    DockerfileStage,
)

KNOWN_INSTRUCTIONS = {
    "FROM",
    "RUN",
    "CMD",
    "LABEL",
    "MAINTAINER",
    "EXPOSE",
    "ENV",
    "ADD",
    "COPY",
    "ENTRYPOINT",
    "VOLUME",
    "USER",
    "WORKDIR",
    "ARG",
    "ONBUILD",
    "STOPSIGNAL",
    "HEALTHCHECK",
    "SHELL",
}


def parse_dockerfile_content(content: str, path: Optional[Path] = None) -> DockerfileParsed:
    """Parse Dockerfile text into structured instructions and stages."""
    target_path = path or Path("Dockerfile")
    lines = content.splitlines()

    instructions: List[DockerfileInstruction] = []
    stages: List[DockerfileStage] = []
    parse_errors: List[str] = []

    current_instruction = ""
    current_args: List[str] = []
    current_raw_lines: List[str] = []
    start_line_num = 0
    current_stage_idx = -1

    def flush_instruction() -> None:
        nonlocal current_instruction, current_args, current_raw_lines, start_line_num, current_stage_idx
        if not current_instruction:
            return

        combined_args = " ".join(current_args).strip()
        raw_combined = "\n".join(current_raw_lines)

        inst = DockerfileInstruction(
            instruction=current_instruction.upper(),
            arguments=combined_args,
            line_number=start_line_num,
            raw_line=raw_combined,
            stage_index=max(0, current_stage_idx),
        )
        instructions.append(inst)

        if current_instruction.upper() == "FROM":
            current_stage_idx += 1
            # Parse FROM image AS stage
            match = re.search(r"^(\S+)(?:\s+[aA][sS]\s+(\S+))?", combined_args)
            base_image = match.group(1) if match else combined_args
            stage_name = match.group(2) if match and match.group(2) else None

            stage = DockerfileStage(
                index=current_stage_idx,
                base_image=base_image,
                line_number=start_line_num,
                name=stage_name,
                instructions=[inst],
            )
            stages.append(stage)
        elif stages:
            stages[-1].instructions.append(inst)

        current_instruction = ""
        current_args = []
        current_raw_lines = []
        start_line_num = 0

    idx = 0
    while idx < len(lines):
        line_num = idx + 1
        raw_line = lines[idx]
        stripped = raw_line.strip()

        # Handle comments or empty lines outside an active continuation
        if not current_instruction and (not stripped or stripped.startswith("#")):
            idx += 1
            continue

        # If starting a new instruction
        if not current_instruction:
            parts = stripped.split(maxsplit=1)
            token = parts[0].upper()

            if token in KNOWN_INSTRUCTIONS:
                current_instruction = token
                start_line_num = line_num
                arg_part = parts[1] if len(parts) > 1 else ""
                current_raw_lines.append(raw_line)

                # Check for line continuation (\ at the end)
                if arg_part.endswith("\\"):
                    current_args.append(arg_part[:-1].strip())
                else:
                    current_args.append(arg_part.strip())
                    flush_instruction()
            else:
                # Malformed or unknown directive
                parse_errors.append(f"Line {line_num}: Unknown directive '{parts[0]}'")
            idx += 1
            continue

        # In the middle of a line continuation
        current_raw_lines.append(raw_line)
        if stripped.endswith("\\"):
            current_args.append(stripped[:-1].strip())
        else:
            current_args.append(stripped)
            flush_instruction()
        idx += 1

    # Flush any dangling instruction
    flush_instruction()

    return DockerfileParsed(
        path=target_path,
        instructions=instructions,
        stages=stages,
        parse_errors=parse_errors,
    )


def parse_dockerfile_file(path: Path) -> DockerfileParsed:
    """Read and parse a Dockerfile from disk."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError) as err:
        return DockerfileParsed(path=path, parse_errors=[str(err)])
    return parse_dockerfile_content(content, path=path)
