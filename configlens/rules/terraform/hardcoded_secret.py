"""Rule detecting hardcoded secrets and credentials in Terraform configurations."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.terraform_models import TerraformBlock, TerraformFile
from configlens.rules.base import Rule, parse_inline_suppressions

SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|private[_-]?key|auth)",
    re.IGNORECASE,
)
SAFE_VALUES = {"", "placeholder", "dummy", "example", "changeme", "none", "null", "true", "false"}


class TerraformHardcodedSecretRule(Rule):
    """Flags hardcoded credentials or secret tokens in Terraform configurations."""

    id = "tf-hardcoded-secret"
    title = "Hardcoded secret in Terraform configuration"
    description = "Resource and provider configurations should not embed plaintext secrets. Use variables or secret stores."
    severity = Severity.CRITICAL
    category = Category.TERRAFORM

    def check(self, file_path: Path, parsed: TerraformFile) -> List[Finding]:
        """Inspect all blocks and nested attributes for sensitive plaintext values."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        def scan_block(block: TerraformBlock) -> None:
            for key, val in block.attributes.items():
                if SENSITIVE_KEY_PATTERN.search(key):
                    str_val = str(val).strip()
                    # Exclude variable or data references
                    is_ref = (
                        str_val.startswith("${")
                        or str_val.startswith("var.")
                        or str_val.startswith("local.")
                        or str_val.startswith("data.")
                        or str_val.startswith("module.")
                    )
                    if not is_ref and str_val.lower() not in SAFE_VALUES and len(str_val) >= 4:
                        attr_line = block.attribute_lines.get(key, block.line_number)
                        if not self.is_line_suppressed(suppressions, attr_line):
                            findings.append(
                                self.create_finding(
                                    file_path=file_path,
                                    line_number=attr_line,
                                    message=(
                                        f"Hardcoded secret detected for attribute '{key}' "
                                        f"in block '{block.identifier}'."
                                    ),
                                    suggested_fix=(
                                        f"Extract secret to variable reference (var.{key}) "
                                        "or an external secret store."
                                    ),
                                )
                            )

            for nested in block.nested_blocks:
                scan_block(nested)

        for top_block in parsed.blocks:
            scan_block(top_block)

        return findings
