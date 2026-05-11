"""Terraform configuration debt rules."""

from configlens.rules.registry import register_rule
from configlens.rules.terraform.hardcoded_secret import TerraformHardcodedSecretRule
from configlens.rules.terraform.missing_prevent_destroy import TerraformMissingPreventDestroyRule
from configlens.rules.terraform.unpinned_provider import TerraformUnpinnedProviderRule
from configlens.rules.terraform.unused_variables import TerraformUnusedVariablesRule

register_rule(TerraformHardcodedSecretRule())
register_rule(TerraformUnpinnedProviderRule())
register_rule(TerraformMissingPreventDestroyRule())
register_rule(TerraformUnusedVariablesRule())

__all__ = [
    "TerraformHardcodedSecretRule",
    "TerraformUnpinnedProviderRule",
    "TerraformMissingPreventDestroyRule",
    "TerraformUnusedVariablesRule",
]
