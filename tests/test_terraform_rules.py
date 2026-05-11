"""Unit tests for Terraform configuration debt rules with good and bad fixtures."""

from pathlib import Path
from configlens.cli import execute_scan
from configlens.models import Category
from configlens.parsers.terraform_parser import parse_terraform_file
from configlens.rules.terraform import (
    TerraformHardcodedSecretRule,
    TerraformMissingPreventDestroyRule,
    TerraformUnpinnedProviderRule,
    TerraformUnusedVariablesRule,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "terraform"
GOOD_TF = FIXTURES_DIR / "good_terraform.tf"
BAD_TF = FIXTURES_DIR / "bad_terraform.tf"


def test_terraform_hardcoded_secret_rule():
    """Verify hardcoded secret rule triggers on plaintext password in resource."""
    rule = TerraformHardcodedSecretRule()

    good_parsed = parse_terraform_file(GOOD_TF)
    assert len(rule.check(GOOD_TF, good_parsed)) == 0

    bad_parsed = parse_terraform_file(BAD_TF)
    findings = rule.check(BAD_TF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "tf-hardcoded-secret"
    assert "password" in findings[0].message


def test_terraform_unpinned_provider_rule():
    """Verify unpinned provider rule triggers when provider version is missing."""
    rule = TerraformUnpinnedProviderRule()

    good_parsed = parse_terraform_file(GOOD_TF)
    assert len(rule.check(GOOD_TF, good_parsed)) == 0

    bad_parsed = parse_terraform_file(BAD_TF)
    findings = rule.check(BAD_TF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "tf-unpinned-provider"
    assert "aws" in findings[0].message


def test_terraform_missing_prevent_destroy_rule():
    """Verify missing prevent_destroy rule triggers on unprotected stateful resource."""
    rule = TerraformMissingPreventDestroyRule()

    good_parsed = parse_terraform_file(GOOD_TF)
    assert len(rule.check(GOOD_TF, good_parsed)) == 0

    bad_parsed = parse_terraform_file(BAD_TF)
    findings = rule.check(BAD_TF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "tf-missing-prevent-destroy"
    assert "aws_db_instance" in findings[0].message


def test_terraform_unused_variables_rule():
    """Verify unused variables rule triggers on declared unreferenced variable."""
    rule = TerraformUnusedVariablesRule()

    good_parsed = parse_terraform_file(GOOD_TF)
    assert len(rule.check(GOOD_TF, good_parsed)) == 0

    bad_parsed = parse_terraform_file(BAD_TF)
    findings = rule.check(BAD_TF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "tf-unused-variables"
    assert "obsolete_api_key" in findings[0].message


def test_terraform_cli_scan_integration():
    """Verify execute_scan detects and processes Terraform files."""
    files, findings = execute_scan(FIXTURES_DIR, only_categories={Category.TERRAFORM})
    assert len(files) == 2
    rule_ids = {f.rule_id for f in findings}
    assert "tf-hardcoded-secret" in rule_ids
    assert "tf-unpinned-provider" in rule_ids
    assert "tf-missing-prevent-destroy" in rule_ids
    assert "tf-unused-variables" in rule_ids
