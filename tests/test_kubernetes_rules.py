"""Unit tests for Kubernetes configuration debt rules with good and bad fixtures."""

from pathlib import Path
from configlens.cli import execute_scan
from configlens.models import Category
from configlens.parsers.k8s_parser import parse_k8s_file
from configlens.rules.kubernetes import (
    K8sLatestImageTagRule,
    K8sMissingProbesRule,
    K8sMissingResourceLimitsRule,
    K8sRootContainerRule,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "kubernetes"
GOOD_K8S = FIXTURES_DIR / "good_k8s.yaml"
BAD_K8S = FIXTURES_DIR / "bad_k8s.yaml"


def test_k8s_missing_resource_limits_rule():
    """Verify rule triggers when CPU or memory limits are omitted."""
    rule = K8sMissingResourceLimitsRule()

    good_parsed = parse_k8s_file(GOOD_K8S)
    assert len(rule.check(GOOD_K8S, good_parsed)) == 0

    bad_parsed = parse_k8s_file(BAD_K8S)
    findings = rule.check(BAD_K8S, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "k8s-missing-resource-limits"
    assert "web" in findings[0].message


def test_k8s_missing_probes_rule():
    """Verify rule triggers when long-running service lacks probes."""
    rule = K8sMissingProbesRule()

    good_parsed = parse_k8s_file(GOOD_K8S)
    assert len(rule.check(GOOD_K8S, good_parsed)) == 0

    bad_parsed = parse_k8s_file(BAD_K8S)
    findings = rule.check(BAD_K8S, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "k8s-missing-probes"
    assert "web" in findings[0].message


def test_k8s_root_container_rule():
    """Verify rule triggers when container lacks non-root security context."""
    rule = K8sRootContainerRule()

    good_parsed = parse_k8s_file(GOOD_K8S)
    assert len(rule.check(GOOD_K8S, good_parsed)) == 0

    bad_parsed = parse_k8s_file(BAD_K8S)
    findings = rule.check(BAD_K8S, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "k8s-root-container"
    assert "web" in findings[0].message


def test_k8s_latest_image_tag_rule():
    """Verify rule triggers when image uses :latest tag."""
    rule = K8sLatestImageTagRule()

    good_parsed = parse_k8s_file(GOOD_K8S)
    assert len(rule.check(GOOD_K8S, good_parsed)) == 0

    bad_parsed = parse_k8s_file(BAD_K8S)
    findings = rule.check(BAD_K8S, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "k8s-latest-image-tag"
    assert "nginx:latest" in findings[0].message


def test_k8s_privileged_container_rule():
    """Verify rule triggers when container runs in privileged mode."""
    from configlens.parsers.k8s_parser import parse_k8s_content
    from configlens.rules.kubernetes.privileged_container import K8sPrivilegedContainerRule

    rule = K8sPrivilegedContainerRule()
    priv_manifest = """apiVersion: v1
kind: Pod
metadata:
  name: priv-pod
spec:
  containers:
    - name: agent
      image: agent:1.0
      securityContext:
        privileged: true
"""
    parsed = parse_k8s_content(priv_manifest)
    findings = rule.check(Path("pod.yaml"), parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "k8s-privileged-container"
    assert "privileged mode" in findings[0].message


def test_k8s_cli_scan_integration():
    """Verify execute_scan detects and analyzes Kubernetes manifests."""
    files, findings = execute_scan(FIXTURES_DIR, only_categories={Category.KUBERNETES})
    assert len(files) == 2
    rule_ids = {f.rule_id for f in findings}
    assert "k8s-missing-resource-limits" in rule_ids
    assert "k8s-missing-probes" in rule_ids
    assert "k8s-root-container" in rule_ids
    assert "k8s-latest-image-tag" in rule_ids
