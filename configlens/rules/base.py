"""Base rule definitions and suppression handling for ConfigLens."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from configlens.models import Category, Finding, Severity

# Pattern for inline suppression comments in configs
SUPPRESSION_PREFIX = "configlens-ignore"


def parse_inline_suppressions(file_path: Path) -> Dict[int, Set[str]]:
    """Parse inline suppression comments from a configuration file.

    Returns mapping of line_number -> set of suppressed rule_ids (empty set = all rules).
    Supports:
        # configlens-ignore
        # configlens-ignore: rule-1, rule-2
    """
    suppressions: Dict[int, Set[str]] = {}
    if not file_path.is_file():
        return suppressions

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                line_num = idx + 1
                if SUPPRESSION_PREFIX in line:
                    parts = line.split(SUPPRESSION_PREFIX, 1)[1].strip()
                    rule_ids: Set[str] = set()
                    if parts.startswith(":"):
                        raw_rules = parts[1:].split()
                        if raw_rules:
                            rule_ids = {r.strip(",").lower() for r in raw_rules[0].split(",")}
                    suppressions[line_num] = rule_ids
    except (OSError, PermissionError):
        pass

    return suppressions


class Rule(ABC):
    """Abstract base class for all ConfigLens configuration debt rules."""

    id: str
    title: str
    description: str
    severity: Severity
    category: Category

    @abstractmethod
    def check(self, file_path: Path, parsed: Any) -> List[Finding]:
        """Inspect parsed file content and return findings."""
        raise NotImplementedError

    def is_line_suppressed(
        self,
        suppressions: Dict[int, Set[str]],
        line_number: int,
    ) -> bool:
        """Check if finding on line_number is suppressed for this rule."""
        # Check current line and line directly above (preceding comment)
        for check_line in (line_number, line_number - 1):
            if check_line in suppressions:
                rule_set = suppressions[check_line]
                if not rule_set or self.id.lower() in rule_set or "*" in rule_set:
                    return True
        return False

    def create_finding(
        self,
        file_path: Path,
        line_number: int,
        message: str,
        suggested_fix: str,
        severity: Optional[Severity] = None,
        column: Optional[int] = None,
    ) -> Finding:
        """Helper to create a typed Finding with default rule properties."""
        return Finding(
            rule_id=self.id,
            title=self.title,
            severity=severity or self.severity,
            category=self.category,
            file_path=file_path,
            line_number=line_number,
            message=message,
            suggested_fix=suggested_fix,
            column=column,
        )
