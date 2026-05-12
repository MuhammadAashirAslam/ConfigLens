"""Rule definitions and registration for ConfigLens."""

from configlens.rules.base import (
    Rule,
    parse_inline_suppressions,
)
from configlens.rules.registry import (
    RuleRegistry,
    default_registry,
    register_rule,
)

# Import all rule packages to register rules with default_registry
import configlens.rules.compose  # noqa: F401
import configlens.rules.dockerfile  # noqa: F401
import configlens.rules.github_actions  # noqa: F401
import configlens.rules.kubernetes  # noqa: F401
import configlens.rules.terraform  # noqa: F401

__all__ = [
    "Rule",
    "parse_inline_suppressions",
    "RuleRegistry",
    "default_registry",
    "register_rule",
]
