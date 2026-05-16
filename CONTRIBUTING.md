# Contributing to ConfigLens

Thank you for contributing to ConfigLens! We welcome rule contributions, parser improvements, and documentation enhancements.

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/MuhammadAashirAslam/ConfigLens.git
cd ConfigLens

# Install with development dependencies
pip install -e ".[dev]"

# Verify the test suite passes
pytest
```

---

## Writing a New Rule

Adding a rule requires three components:
1. **Rule Class**: Implement a `Rule` subclass in `configlens/rules/<category>/`.
2. **Fixtures**: Add a "good" (clean) and "bad" (violating) fixture in `tests/fixtures/<category>/`.
3. **Tests**: Add unit test verifying the rule passes on good fixture and triggers on bad fixture.

### Rule Template

```python
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.rules.base import Rule, parse_inline_suppressions


class MyNewRule(Rule):
    """Rule documentation explaining the debt anti-pattern."""

    id = "my-new-rule-id"
    title = "Human-readable short title"
    description = "Detailed explanation of why this pattern introduces technical debt."
    severity = Severity.HIGH  # CRITICAL, HIGH, MEDIUM, or LOW
    category = Category.DOCKERFILE  # Target category

    def check(self, file_path: Path, parsed: Any) -> List[Finding]:
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        # Inspect parsed IR model...
        # If violation detected:
        if not self.is_line_suppressed(suppressions, line_number):
            findings.append(
                self.create_finding(
                    file_path=file_path,
                    line_number=line_number,
                    message="Explanation of the specific violation found.",
                    suggested_fix="Concrete one-line remediation action.",
                )
            )

        return findings
```

### Registration

Register your rule in `configlens/rules/<category>/__init__.py`:

```python
from configlens.rules.registry import register_rule
from configlens.rules.<category>.my_new_rule import MyNewRule

register_rule(MyNewRule())
```

---

## Pull Request Guidelines

- **One rule or feature per PR.**
- **No network calls in rules or parsers.** Static analysis runs strictly offline.
- **Always provide good and bad fixtures.**
- **Every finding must include a `suggested_fix` string.**
- Ensure `pytest` passes with 100% success before opening a PR.
