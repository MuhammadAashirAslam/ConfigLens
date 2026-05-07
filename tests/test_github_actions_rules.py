"""Unit tests for GitHub Actions configuration debt rules with good and bad fixtures."""

from pathlib import Path
from configlens.parsers.workflow_parser import parse_workflow_file
from configlens.rules.github_actions import (
    BroadPermissionsRule,
    DuplicateStepNamesRule,
    MissingDependencyCachingRule,
    MissingJobTimeoutRule,
    PlaintextHardcodedSecretRule,
    UnpinnedActionVersionRule,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "github_actions"
GOOD_WORKFLOW = FIXTURES_DIR / "good_workflow.yml"
BAD_WORKFLOW = FIXTURES_DIR / "bad_workflow.yml"


def test_unpinned_action_version_rule():
    """Verify unpinned action version rule triggers on bad fixture and passes on good."""
    rule = UnpinnedActionVersionRule()

    good_parsed = parse_workflow_file(GOOD_WORKFLOW)
    good_findings = rule.check(GOOD_WORKFLOW, good_parsed)
    assert len(good_findings) == 0

    bad_parsed = parse_workflow_file(BAD_WORKFLOW)
    bad_findings = rule.check(BAD_WORKFLOW, bad_parsed)
    assert len(bad_findings) == 1
    assert bad_findings[0].rule_id == "gha-unpinned-action"
    assert "actions/checkout@v4" in bad_findings[0].message
    assert "suggested_fix" in bad_findings[0].to_dict()


def test_missing_caching_rule():
    """Verify missing dependency caching rule triggers when npm install lacks cache."""
    rule = MissingDependencyCachingRule()

    good_parsed = parse_workflow_file(GOOD_WORKFLOW)
    assert len(rule.check(GOOD_WORKFLOW, good_parsed)) == 0

    bad_parsed = parse_workflow_file(BAD_WORKFLOW)
    findings = rule.check(BAD_WORKFLOW, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "gha-missing-caching"


def test_broad_permissions_rule():
    """Verify overly broad permissions rule triggers on write-all."""
    rule = BroadPermissionsRule()

    good_parsed = parse_workflow_file(GOOD_WORKFLOW)
    assert len(rule.check(GOOD_WORKFLOW, good_parsed)) == 0

    bad_parsed = parse_workflow_file(BAD_WORKFLOW)
    findings = rule.check(BAD_WORKFLOW, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "gha-broad-permissions"
    assert "write-all" in findings[0].message


def test_missing_timeout_rule():
    """Verify missing job timeout rule triggers when timeout-minutes is absent."""
    rule = MissingJobTimeoutRule()

    good_parsed = parse_workflow_file(GOOD_WORKFLOW)
    assert len(rule.check(GOOD_WORKFLOW, good_parsed)) == 0

    bad_parsed = parse_workflow_file(BAD_WORKFLOW)
    findings = rule.check(BAD_WORKFLOW, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "gha-missing-timeout"


def test_hardcoded_secret_rule():
    """Verify plaintext hardcoded secret rule triggers on PAT token."""
    rule = PlaintextHardcodedSecretRule()

    good_parsed = parse_workflow_file(GOOD_WORKFLOW)
    assert len(rule.check(GOOD_WORKFLOW, good_parsed)) == 0

    bad_parsed = parse_workflow_file(BAD_WORKFLOW)
    findings = rule.check(BAD_WORKFLOW, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "gha-hardcoded-secret"


def test_duplicate_step_names_rule():
    """Verify duplicate step names rule triggers when same name is used twice."""
    rule = DuplicateStepNamesRule()

    good_parsed = parse_workflow_file(GOOD_WORKFLOW)
    assert len(rule.check(GOOD_WORKFLOW, good_parsed)) == 0

    bad_parsed = parse_workflow_file(BAD_WORKFLOW)
    findings = rule.check(BAD_WORKFLOW, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "gha-duplicate-step-names"
    assert "Build project" in findings[0].message
