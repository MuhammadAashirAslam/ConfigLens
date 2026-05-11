"""Rule detecting missing lifecycle.prevent_destroy on stateful Terraform resources."""

from pathlib import Path
from typing import List, Set
from configlens.models import Category, Finding, Severity
from configlens.parsers.terraform_models import TerraformFile
from configlens.rules.base import Rule, parse_inline_suppressions

# Stateful resource types that carry high risk of permanent data loss
STATEFUL_RESOURCE_TYPES: Set[str] = {
    # AWS
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_s3_bucket",
    "aws_dynamodb_table",
    "aws_elasticache_cluster",
    "aws_ebs_volume",
    # GCP
    "google_sql_database_instance",
    "google_storage_bucket",
    "google_bigtable_instance",
    # Azure
    "azurerm_postgresql_server",
    "azurerm_mysql_server",
    "azurerm_mssql_server",
    "azurerm_storage_account",
}


class TerraformMissingPreventDestroyRule(Rule):
    """Flags stateful cloud resources missing 'lifecycle { prevent_destroy = true }'."""

    id = "tf-missing-prevent-destroy"
    title = "Missing prevent_destroy lifecycle protection on stateful resource"
    description = (
        "Stateful resources such as databases and object storage buckets should define "
        "'lifecycle { prevent_destroy = true }' to prevent accidental destruction."
    )
    severity = Severity.HIGH
    category = Category.TERRAFORM

    def check(self, file_path: Path, parsed: TerraformFile) -> List[Finding]:
        """Check all resources of stateful types for prevent_destroy lifecycle attribute."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for res in parsed.resources:
            res_type = res.labels[0] if res.labels else ""
            if res_type in STATEFUL_RESOURCE_TYPES:
                lifecycle_block = res.get_nested_block("lifecycle")
                has_prevent_destroy = (
                    lifecycle_block is not None
                    and lifecycle_block.attributes.get("prevent_destroy", "").lower() == "true"
                )

                if not has_prevent_destroy:
                    if not self.is_line_suppressed(suppressions, res.line_number):
                        findings.append(
                            self.create_finding(
                                file_path=file_path,
                                line_number=res.line_number,
                                message=(
                                    f"Stateful resource '{res.identifier}' does not have "
                                    "'lifecycle { prevent_destroy = true }' configured."
                                ),
                                suggested_fix=(
                                    "Add 'lifecycle { prevent_destroy = true }' block inside the "
                                    f"'{res_type}' declaration."
                                ),
                            )
                        )

        return findings
