"""Rule detecting unpinned or missing provider versions in Terraform configurations."""

from pathlib import Path
from typing import List, Set
from configlens.models import Category, Finding, Severity
from configlens.parsers.terraform_models import TerraformBlock, TerraformFile
from configlens.rules.base import Rule, parse_inline_suppressions


def _is_pinned_version(version_str: str) -> bool:
    """Check if version constraint represents a pinned or bounded version."""
    v = version_str.strip().strip("\"'")
    if not v or v in ("latest", "*"):
        return False
    if v.startswith(">=") and "<" not in v:
        return False
    if v.startswith("~>") or v.startswith("=") or (v[0].isdigit() and not any(op in v for op in (">", "<", "*"))):
        return True
    return False


class TerraformUnpinnedProviderRule(Rule):
    """Flags providers without pinned version constraints."""

    id = "tf-unpinned-provider"
    title = "Unpinned or missing provider version"
    description = "Terraform providers should pin versions using pessimistic constraints (~> X.Y) or exact versions (= X.Y.Z)."
    severity = Severity.HIGH
    category = Category.TERRAFORM

    def check(self, file_path: Path, parsed: TerraformFile) -> List[Finding]:
        """Verify that all declared providers have pinned version constraints."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        # 1. Collect versions declared in required_providers block
        pinned_required_providers: Set[str] = set()

        for b in parsed.blocks:
            if b.block_type == "terraform":
                for nb in b.nested_blocks:
                    if nb.block_type == "required_providers":
                        for prov_block in nb.nested_blocks:
                            prov_name = prov_block.block_type
                            v = prov_block.attributes.get("version", "")
                            if v and _is_pinned_version(v):
                                pinned_required_providers.add(prov_name)
                            else:
                                line = prov_block.attribute_lines.get("version", prov_block.line_number)
                                if not self.is_line_suppressed(suppressions, line):
                                    findings.append(
                                        self.create_finding(
                                            file_path=file_path,
                                            line_number=line,
                                            message=f"Provider '{prov_name}' has unpinned version constraint '{v or 'missing'}'.",
                                            suggested_fix=f"Pin version with pessimistic operator (e.g., version = '~> X.Y') for '{prov_name}'.",
                                        )
                                    )

        # 2. Check standalone provider blocks
        for prov in parsed.providers:
            prov_name = prov.labels[0] if prov.labels else "unknown"
            if prov_name in pinned_required_providers:
                continue

            v = prov.attributes.get("version", "")
            if not v or not _is_pinned_version(v):
                line = prov.attribute_lines.get("version", prov.line_number)
                if not self.is_line_suppressed(suppressions, line):
                    findings.append(
                        self.create_finding(
                            file_path=file_path,
                            line_number=line,
                            message=f"Provider '{prov_name}' does not specify a pinned version constraint.",
                            suggested_fix=f"Add a pinned version constraint to provider '{prov_name}' or declare it in required_providers (~> X.Y).",
                        )
                    )

        return findings
