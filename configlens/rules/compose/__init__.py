"""Docker Compose configuration debt rules."""

from configlens.rules.compose.hardcoded_credentials import ComposeHardcodedCredentialsRule

__all__ = [
    "ComposeHardcodedCredentialsRule",
]
