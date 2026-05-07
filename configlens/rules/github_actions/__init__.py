"""GitHub Actions configuration debt rules."""

from configlens.rules.github_actions.unpinned_action import UnpinnedActionVersionRule

__all__ = [
    "UnpinnedActionVersionRule",
]
