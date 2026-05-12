"""Kubernetes configuration debt rules."""

from configlens.rules.registry import register_rule
from configlens.rules.kubernetes.missing_probes import K8sMissingProbesRule
from configlens.rules.kubernetes.missing_resource_limits import K8sMissingResourceLimitsRule

register_rule(K8sMissingResourceLimitsRule())
register_rule(K8sMissingProbesRule())

__all__ = [
    "K8sMissingResourceLimitsRule",
    "K8sMissingProbesRule",
]
