"""Dockerfile configuration debt rules."""

from configlens.rules.dockerfile.baked_secrets import DockerfileBakedSecretsRule
from configlens.rules.dockerfile.latest_tag import DockerfileLatestTagRule
from configlens.rules.dockerfile.missing_dockerignore import MissingDockerignoreRule
from configlens.rules.dockerfile.missing_healthcheck import MissingHealthcheckRule
from configlens.rules.dockerfile.multiple_run import MultipleRunLayersRule
from configlens.rules.dockerfile.running_as_root import DockerfileRunningAsRootRule
from configlens.rules.dockerfile.uncached_pkg_manager import UncachedPkgManagerRule
from configlens.rules.registry import register_rule

ALL_DOCKERFILE_RULES = [
    DockerfileLatestTagRule(),
    DockerfileRunningAsRootRule(),
    MultipleRunLayersRule(),
    MissingHealthcheckRule(),
    DockerfileBakedSecretsRule(),
    UncachedPkgManagerRule(),
    MissingDockerignoreRule(),
]

for rule in ALL_DOCKERFILE_RULES:
    register_rule(rule)

__all__ = [
    "DockerfileLatestTagRule",
    "DockerfileRunningAsRootRule",
    "MultipleRunLayersRule",
    "MissingHealthcheckRule",
    "DockerfileBakedSecretsRule",
    "UncachedPkgManagerRule",
    "MissingDockerignoreRule",
    "ALL_DOCKERFILE_RULES",
]
