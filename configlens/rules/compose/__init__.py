"""Docker Compose configuration debt rules."""

from configlens.rules.compose.broad_ports import ComposeBroadPortsRule
from configlens.rules.compose.hardcoded_credentials import ComposeHardcodedCredentialsRule
from configlens.rules.compose.missing_restart import ComposeMissingRestartRule
from configlens.rules.compose.service_image import ComposeLatestTagRule
from configlens.rules.registry import register_rule

ALL_COMPOSE_RULES = [
    ComposeHardcodedCredentialsRule(),
    ComposeMissingRestartRule(),
    ComposeLatestTagRule(),
    ComposeBroadPortsRule(),
]

for rule in ALL_COMPOSE_RULES:
    register_rule(rule)

__all__ = [
    "ComposeHardcodedCredentialsRule",
    "ComposeMissingRestartRule",
    "ComposeLatestTagRule",
    "ComposeBroadPortsRule",
    "ALL_COMPOSE_RULES",
]
