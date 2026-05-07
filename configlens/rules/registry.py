"""Rule registration and management system for ConfigLens."""

from typing import Dict, List, Optional
from configlens.models import Category
from configlens.rules.base import Rule


class RuleRegistry:
    """Registry maintaining active rules organized by category and rule ID."""

    def __init__(self) -> None:
        self._rules_by_id: Dict[str, Rule] = {}
        self._rules_by_category: Dict[Category, List[Rule]] = {
            Category.GITHUB_ACTIONS: [],
            Category.DOCKERFILE: [],
            Category.DOCKER_COMPOSE: [],
            Category.TERRAFORM: [],
            Category.KUBERNETES: [],
        }

    def register(self, rule: Rule) -> None:
        """Register a new rule instance in the registry."""
        rule_key = rule.id.lower()
        if rule_key in self._rules_by_id:
            # Replace existing rule with updated one
            old_rule = self._rules_by_id[rule_key]
            if old_rule.category in self._rules_by_category:
                self._rules_by_category[old_rule.category] = [
                    r for r in self._rules_by_category[old_rule.category] if r.id.lower() != rule_key
                ]

        self._rules_by_id[rule_key] = rule
        if rule.category in self._rules_by_category:
            self._rules_by_category[rule.category].append(rule)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Retrieve a registered rule by its ID."""
        return self._rules_by_id.get(rule_id.lower())

    def get_rules_for_category(self, category: Category) -> List[Rule]:
        """Retrieve all rules registered for a given category."""
        return list(self._rules_by_category.get(category, []))

    def all_rules(self) -> List[Rule]:
        """Retrieve all registered rules."""
        return list(self._rules_by_id.values())

    def clear(self) -> None:
        """Clear all registered rules."""
        self._rules_by_id.clear()
        for cat in self._rules_by_category:
            self._rules_by_category[cat].clear()


# Global default registry instance
default_registry = RuleRegistry()


def register_rule(rule: Rule) -> Rule:
    """Convenience decorator or function to register a rule in the default registry."""
    default_registry.register(rule)
    return rule
