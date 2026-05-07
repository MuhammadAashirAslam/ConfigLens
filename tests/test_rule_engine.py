"""Unit tests for Rule engine core, suppression parsing, and configuration loader."""

from pathlib import Path
from configlens.config import ConfigLensConfig
from configlens.models import Category, Finding, Severity
from configlens.rules.base import Rule, parse_inline_suppressions
from configlens.rules.registry import RuleRegistry


class DummyCheckRule(Rule):
    id = "dummy-rule"
    title = "Dummy check rule"
    description = "Flags any occurrence of TODO"
    severity = Severity.MEDIUM
    category = Category.GITHUB_ACTIONS

    def check(self, file_path: Path, parsed: dict) -> list[Finding]:
        findings = []
        suppressions = parse_inline_suppressions(file_path)
        if "TODO" in parsed.get("text", ""):
            if not self.is_line_suppressed(suppressions, 5):
                findings.append(
                    self.create_finding(
                        file_path=file_path,
                        line_number=5,
                        message="Found TODO",
                        suggested_fix="Resolve TODO item",
                    )
                )
        return findings


def test_rule_registry():
    """Verify rules can be registered and retrieved by category and ID."""
    reg = RuleRegistry()
    rule = DummyCheckRule()
    reg.register(rule)

    assert reg.get_rule("dummy-rule") is rule
    assert reg.get_rule("DUMMY-RULE") is rule
    assert rule in reg.get_rules_for_category(Category.GITHUB_ACTIONS)
    assert len(reg.get_rules_for_category(Category.DOCKERFILE)) == 0


def test_inline_suppressions(tmp_path: Path):
    """Verify inline suppression comments are parsed and respected."""
    fixture = tmp_path / "config.yml"
    fixture.write_text(
        "line 1\n"
        "# configlens-ignore: dummy-rule\n"
        "line 3: TODO\n"
        "# configlens-ignore\n"
        "line 5: TODO\n",
        encoding="utf-8",
    )

    suppressions = parse_inline_suppressions(fixture)
    assert 2 in suppressions
    assert "dummy-rule" in suppressions[2]
    assert 4 in suppressions
    assert len(suppressions[4]) == 0  # blanket ignore

    rule = DummyCheckRule()
    # Line 3 preceded by suppression on line 2
    assert rule.is_line_suppressed(suppressions, 3) is True
    # Line 5 preceded by suppression on line 4
    assert rule.is_line_suppressed(suppressions, 5) is True
    # Line 1 not suppressed
    assert rule.is_line_suppressed(suppressions, 1) is False


def test_config_loader_and_overrides(tmp_path: Path):
    """Verify .configlens.yml parses rule enable/disable and severity overrides."""
    config_file = tmp_path / ".configlens.yml"
    config_file.write_text(
        """rules:
  dummy-rule:
    enabled: true
    severity: critical
  gha-unpinned-action:
    enabled: false
fail_on: high
ignore:
  - "*.tmp"
""",
        encoding="utf-8",
    )

    cfg = ConfigLensConfig.load(config_file)
    assert cfg.is_rule_enabled("dummy-rule") is True
    assert cfg.is_rule_enabled("gha-unpinned-action") is False
    assert cfg.is_rule_enabled("unknown-rule") is True  # default enabled

    assert cfg.get_severity("dummy-rule", Severity.MEDIUM) == Severity.CRITICAL
    assert cfg.get_severity("unknown-rule", Severity.LOW) == Severity.LOW
    assert cfg.fail_on == Severity.HIGH
    assert "*.tmp" in cfg.ignore_patterns
