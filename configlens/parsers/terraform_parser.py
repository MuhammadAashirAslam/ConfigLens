"""Lightweight HCL parser for Terraform configuration files with line tracking."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from configlens.parsers.terraform_models import TerraformBlock, TerraformFile

BLOCK_HEADER_RE = re.compile(
    r'^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s+(?:("([^"]+)"|([a-zA-Z0-9_-]+))\s*)*(?:("([^"]+)"|([a-zA-Z0-9_-]+))\s*)?\{\s*$'
)
ATTR_RE = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(.+)$')


def parse_terraform_content(content: str, path: Optional[Path] = None) -> TerraformFile:
    """Parse HCL text into typed TerraformFile with block and attribute line numbers."""
    target_path = path or Path("main.tf")
    lines = content.splitlines()

    blocks: List[TerraformBlock] = []
    parse_errors: List[str] = []

    block_stack: List[TerraformBlock] = []
    raw_lines_stack: List[List[str]] = []

    for idx, line in enumerate(lines):
        line_num = idx + 1
        stripped = line.strip()

        # Skip comments and empty lines outside blocks
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        # Check for block open
        if stripped.endswith("{"):
            # Extract block type and labels
            # e.g.: resource "aws_s3_bucket" "bucket" {
            tokens = []
            header_str = stripped[:-1].strip()
            # Split respecting quotes
            parts = re.findall(r'"([^"]*)"|(\S+)', header_str)
            for quoted, unquoted in parts:
                tokens.append(quoted if quoted else unquoted)

            if tokens:
                b_type = tokens[0]
                b_labels = tokens[1:]
                new_block = TerraformBlock(
                    block_type=b_type,
                    labels=b_labels,
                    line_number=line_num,
                )
                if block_stack:
                    block_stack[-1].nested_blocks.append(new_block)
                block_stack.append(new_block)
                raw_lines_stack.append([line])
                continue

        # Check for block close
        if stripped == "}" or stripped.endswith("}"):
            if block_stack:
                closed_block = block_stack.pop()
                if raw_lines_stack:
                    closed_block.raw_content = "\n".join(raw_lines_stack.pop())
                if not block_stack:
                    blocks.append(closed_block)
            continue

        # Inside an active block, check for attributes: key = value
        if block_stack:
            raw_lines_stack[-1].append(line)
            m = ATTR_RE.match(stripped)
            if m:
                key = m.group(1).strip()
                raw_val = m.group(2).strip()
                clean_val = raw_val.strip("\"'")
                block_stack[-1].attributes[key] = clean_val
                block_stack[-1].attribute_lines[key] = line_num

    return TerraformFile(
        path=target_path,
        blocks=blocks,
        raw_text=content,
        parse_errors=parse_errors,
    )


def parse_terraform_file(path: Path) -> TerraformFile:
    """Read and parse a Terraform .tf or .tfvars file from disk."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError) as err:
        return TerraformFile(path=path, parse_errors=[str(err)])
    return parse_terraform_content(content, path=path)
