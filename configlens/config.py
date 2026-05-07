"""Configuration loader and rule customization for ConfigLens."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from configlens.models import Severity


@dataclass
class RuleConfig:
    """Configuration settings for a single rule."""

    enabled: bool = True
    severity: Optional[Severity] = None


@dataclass
class ConfigLensConfig:
    """Global configuration parsed from .configlens.yml."""

    rules: Dict[str, RuleConfig] = field(default_factory=dict)
    ignore_patterns: List[str] = field(default_factory=list)
    fail_on: Optional[Severity] = None

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled in the configuration."""
        key = rule_id.lower()
        if key in self.rules:
            return self.rules[key].enabled
        return True

    def get_severity(self, rule_id: str, default: Severity) -> Severity:
        """Get the effective severity for a rule, considering overrides."""
        key = rule_id.lower()
        if key in self.rules and self.rules[key].severity is not None:
            return self.rules[key].severity  # type: ignore
        return default

    @classmethod
    def load(cls, config_path: Optional[Path] = None, root_dir: Optional[Path] = None) -> "ConfigLensConfig":
        """Load ConfigLens configuration from a file or search for .configlens.yml."""
        target: Optional[Path] = None
        if config_path and config_path.is_file():
            target = config_path
        elif root_dir:
            for candidate in [".configlens.yml", ".configlens.yaml"]:
                p = root_dir / candidate
                if p.is_file():
                    target = p
                    break

        if not target or not target.is_file():
            return cls()

        try:
            content = target.read_text(encoding="utf-8", errors="ignore")
            data = yaml.safe_load(content)
        except (OSError, yaml.YAMLError):
            return cls()

        if not isinstance(data, dict):
            return cls()

        rules: Dict[str, RuleConfig] = {}
        raw_rules = data.get("rules", {})
        if isinstance(raw_rules, dict):
            for r_id, r_conf in raw_rules.items():
                if isinstance(r_conf, dict):
                    enabled = bool(r_conf.get("enabled", True))
                    sev_str = r_conf.get("severity")
                    sev: Optional[Severity] = None
                    if sev_str:
                        try:
                            sev = Severity(str(sev_str).lower())
                        except ValueError:
                            sev = None
                    rules[str(r_id).lower()] = RuleConfig(enabled=enabled, severity=sev)
                elif isinstance(r_conf, bool):
                    rules[str(r_id).lower()] = RuleConfig(enabled=r_conf)

        ignore_raw = data.get("ignore", [])
        ignore_patterns = [str(x) for x in ignore_raw] if isinstance(ignore_raw, list) else []

        fail_on_raw = data.get("fail_on")
        fail_on: Optional[Severity] = None
        if fail_on_raw:
            try:
                fail_on = Severity(str(fail_on_raw).lower())
            except ValueError:
                fail_on = None

        return cls(rules=rules, ignore_patterns=ignore_patterns, fail_on=fail_on)
