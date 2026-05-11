"""Typed intermediate representation (IR) models for Terraform HCL configurations."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TerraformBlock:
    """Represents a top-level or nested block in an HCL file."""

    block_type: str
    labels: List[str]
    line_number: int
    attributes: Dict[str, Any] = field(default_factory=dict)
    attribute_lines: Dict[str, int] = field(default_factory=dict)
    raw_content: str = ""
    nested_blocks: List["TerraformBlock"] = field(default_factory=list)

    @property
    def identifier(self) -> str:
        """Full label identifier (e.g., 'aws_s3_bucket.my_bucket')."""
        return ".".join(self.labels) if self.labels else self.block_type

    def get_nested_block(self, block_type: str) -> Optional["TerraformBlock"]:
        """Find first nested block matching the given block type."""
        for block in self.nested_blocks:
            if block.block_type == block_type:
                return block
        return None


@dataclass
class TerraformFile:
    """Represents a parsed Terraform configuration file (.tf or .tfvars)."""

    path: Path
    blocks: List[TerraformBlock] = field(default_factory=list)
    raw_text: str = ""
    parse_errors: List[str] = field(default_factory=list)

    @property
    def resources(self) -> List[TerraformBlock]:
        """Convenience property for resource blocks."""
        return [b for b in self.blocks if b.block_type == "resource"]

    @property
    def variables(self) -> List[TerraformBlock]:
        """Convenience property for variable blocks."""
        return [b for b in self.blocks if b.block_type == "variable"]

    @property
    def providers(self) -> List[TerraformBlock]:
        """Convenience property for provider blocks."""
        return [b for b in self.blocks if b.block_type == "provider"]
