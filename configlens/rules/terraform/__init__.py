"""Terraform configuration debt rules."""

from configlens.rules.registry import register_rule
from configlens.rules.terraform.hardcoded_secret import TerraformHardcodedSecretRule
from configlens.rules.terraform.unpinned_provider import TerraformUnpinnedProviderRule

register_rule(TerraformHardcodedSecretRule())
register_rule(TerraformUnpinnedProviderRule())

__all__ = [
    "TerraformHardcodedSecretRule",
    "TerraformUnpinnedProviderRule",
]
