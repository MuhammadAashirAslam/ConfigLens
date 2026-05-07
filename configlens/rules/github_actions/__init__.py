"""GitHub Actions configuration debt rules."""

from configlens.rules.github_actions.broad_permissions import BroadPermissionsRule
from configlens.rules.github_actions.duplicate_steps import DuplicateStepNamesRule
from configlens.rules.github_actions.hardcoded_secret import PlaintextHardcodedSecretRule
from configlens.rules.github_actions.missing_caching import MissingDependencyCachingRule
from configlens.rules.github_actions.missing_timeout import MissingJobTimeoutRule
from configlens.rules.github_actions.unpinned_action import UnpinnedActionVersionRule
from configlens.rules.registry import register_rule

# Automatically register all GitHub Actions rules into the default registry
ALL_GHA_RULES = [
    UnpinnedActionVersionRule(),
    MissingDependencyCachingRule(),
    BroadPermissionsRule(),
    MissingJobTimeoutRule(),
    PlaintextHardcodedSecretRule(),
    DuplicateStepNamesRule(),
]

for rule in ALL_GHA_RULES:
    register_rule(rule)

__all__ = [
    "UnpinnedActionVersionRule",
    "MissingDependencyCachingRule",
    "BroadPermissionsRule",
    "MissingJobTimeoutRule",
    "PlaintextHardcodedSecretRule",
    "DuplicateStepNamesRule",
    "ALL_GHA_RULES",
]
