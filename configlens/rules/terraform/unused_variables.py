"""Rule detecting declared Terraform variables that are never referenced."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.terraform_models import TerraformFile
from configlens.rules.base import Rule, parse_inline_suppressions


class TerraformUnusedVariablesRule(Rule):
    """Flags variables declared in Terraform configurations that are never used."""

    id = "tf-unused-variables"
    title = "Unused Terraform variable declaration"
    description = "Declared input variables should be referenced in resources, locals, or outputs, or removed if obsolete."
    severity = Severity.LOW
    category = Category.TERRAFORM

    def check(self, file_path: Path, parsed: TerraformFile) -> List[Finding]:
        """Check all declared variable blocks for usage in the file."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for var_block in parsed.variables:
            var_name = var_block.labels[0] if var_block.labels else ""
            if not var_name:
                continue

            # Look for var.<name> reference
            usage_pattern = re.compile(rf"\bvar\.{re.escape(var_name)}\b")
            if not usage_pattern.search(parsed.raw_text):
                if not self.is_line_suppressed(suppressions, var_block.line_number):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=var_block.line_number,
                            message=f"Variable '{var_name}' is declared but never referenced in configuration.",
                            suggested_fix=f"Reference variable with 'var.{var_name}' or remove unused variable declaration.",
                        )
                    )

        return findings
