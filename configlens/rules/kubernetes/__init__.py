"""Kubernetes configuration debt rules."""

from configlens.rules.registry import register_rule
from configlens.rules.kubernetes.latest_image_tag import K8sLatestImageTagRule
from configlens.rules.kubernetes.missing_probes import K8sMissingProbesRule
from configlens.rules.kubernetes.missing_resource_limits import K8sMissingResourceLimitsRule
from configlens.rules.kubernetes.root_container import K8sRootContainerRule

register_rule(K8sMissingResourceLimitsRule())
register_rule(K8sMissingProbesRule())
register_rule(K8sRootContainerRule())
register_rule(K8sLatestImageTagRule())

__all__ = [
    "K8sMissingResourceLimitsRule",
    "K8sMissingProbesRule",
    "K8sRootContainerRule",
    "K8sLatestImageTagRule",
]
