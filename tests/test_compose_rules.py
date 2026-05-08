"""Unit tests for Docker Compose configuration debt rules with good and bad fixtures."""

from pathlib import Path
from configlens.parsers.compose_parser import parse_compose_file
from configlens.rules.compose import (
    ComposeBroadPortsRule,
    ComposeHardcodedCredentialsRule,
    ComposeLatestTagRule,
    ComposeMissingRestartRule,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "compose"
GOOD_COMPOSE = FIXTURES_DIR / "good_compose.yml"
BAD_COMPOSE = FIXTURES_DIR / "bad_compose.yml"


def test_compose_hardcoded_credentials_rule():
    """Verify hardcoded credentials rule triggers on plaintext DB password."""
    rule = ComposeHardcodedCredentialsRule()

    good_parsed = parse_compose_file(GOOD_COMPOSE)
    assert len(rule.check(GOOD_COMPOSE, good_parsed)) == 0

    bad_parsed = parse_compose_file(BAD_COMPOSE)
    findings = rule.check(BAD_COMPOSE, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "compose-hardcoded-credentials"
    assert "POSTGRES_PASSWORD" in findings[0].message


def test_compose_missing_restart_rule():
    """Verify missing restart policy rule triggers when restart is disabled or missing."""
    rule = ComposeMissingRestartRule()

    good_parsed = parse_compose_file(GOOD_COMPOSE)
    assert len(rule.check(GOOD_COMPOSE, good_parsed)) == 0

    bad_parsed = parse_compose_file(BAD_COMPOSE)
    findings = rule.check(BAD_COMPOSE, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "compose-missing-restart"


def test_compose_latest_tag_rule():
    """Verify latest tag rule triggers on postgres:latest."""
    rule = ComposeLatestTagRule()

    good_parsed = parse_compose_file(GOOD_COMPOSE)
    assert len(rule.check(GOOD_COMPOSE, good_parsed)) == 0

    bad_parsed = parse_compose_file(BAD_COMPOSE)
    findings = rule.check(BAD_COMPOSE, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "compose-latest-tag"
    assert "postgres:latest" in findings[0].message


def test_compose_broad_ports_rule():
    """Verify broad port exposure triggers on unconstrained database port."""
    rule = ComposeBroadPortsRule()

    good_parsed = parse_compose_file(GOOD_COMPOSE)
    assert len(rule.check(GOOD_COMPOSE, good_parsed)) == 0

    bad_parsed = parse_compose_file(BAD_COMPOSE)
    findings = rule.check(BAD_COMPOSE, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "compose-broad-ports"
    assert "5432:5432" in findings[0].message
