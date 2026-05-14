"""CLI entrypoint and scan command for ConfigLens."""

import sys
from pathlib import Path
from typing import Any, List, Optional, Set
import click

from configlens import __version__
from configlens.config import ConfigLensConfig
from configlens.discovery import discover_files
from configlens.models import Category, Finding, Severity
from configlens.parsers import (
    parse_compose_file,
    parse_dockerfile_file,
    parse_k8s_file,
    parse_terraform_file,
    parse_workflow_file,
)
from configlens.reporters import (
    render_json_report,
    render_sarif_report,
    render_terminal_report,
)
import configlens.rules  # Ensures all rules are registered
from configlens.rules.registry import default_registry


@click.group()
@click.version_option(version=__version__, prog_name="configlens")
def main() -> None:
    """ConfigLens: Static Analysis & Technical Debt Detection for DevOps Configuration."""
    pass


def execute_scan(
    target_path: Path,
    only_categories: Optional[Set[Category]] = None,
    ignore_file: Optional[Path] = None,
    config: Optional[ConfigLensConfig] = None,
) -> tuple[list, list[Finding]]:
    """Scan directory and run all active rules against discovered DevOps configurations."""
    cfg = config or ConfigLensConfig.load(root_dir=target_path)
    discovered_files = discover_files(target_path, only=only_categories, ignore_file=ignore_file)

    all_findings: List[Finding] = []

    for df in discovered_files:
        rules = default_registry.get_rules_for_category(df.category)
        if not rules:
            continue

        # Parse file according to category
        parsed_content: Any = None
        if df.category == Category.GITHUB_ACTIONS:
            parsed_content = parse_workflow_file(df.path)
        elif df.category == Category.DOCKERFILE:
            parsed_content = parse_dockerfile_file(df.path)
        elif df.category == Category.DOCKER_COMPOSE:
            parsed_content = parse_compose_file(df.path)
        elif df.category == Category.TERRAFORM:
            parsed_content = parse_terraform_file(df.path)
        elif df.category == Category.KUBERNETES:
            parsed_content = parse_k8s_file(df.path)

        if parsed_content is None:
            continue

        for rule in rules:
            if not cfg.is_rule_enabled(rule.id):
                continue

            findings = rule.check(df.path, parsed_content)
            # Check for severity override from config
            effective_sev = cfg.get_severity(rule.id, rule.severity)
            if effective_sev != rule.severity:
                findings = [
                    Finding(
                        rule_id=f.rule_id,
                        title=f.title,
                        severity=effective_sev,
                        category=f.category,
                        file_path=f.file_path,
                        line_number=f.line_number,
                        message=f.message,
                        suggested_fix=f.suggested_fix,
                        column=f.column,
                    )
                    for f in findings
                ]

            all_findings.extend(findings)

    # Deterministic sort by file relative path, line number, rule_id
    all_findings.sort(key=lambda x: (str(x.file_path), x.line_number, x.rule_id))
    return discovered_files, all_findings


@main.command(name="scan")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path))
@click.option(
    "--only",
    help="Comma-separated list of categories to scan (e.g., github-actions,dockerfile).",
    default=None,
    type=str,
)
@click.option(
    "--ignore",
    "ignore_file",
    help="Path to custom ignore file (e.g., .configlensignore).",
    default=None,
    type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json", "sarif"], case_sensitive=False),
    default="terminal",
    help="Output report format.",
)
@click.option(
    "--fail-on",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    default="high",
    help="Minimum severity threshold to exit with non-zero status code.",
)
def scan_command(
    path: Path,
    only: Optional[str],
    ignore_file: Optional[Path],
    output_format: str,
    fail_on: str,
) -> None:
    """Scan a repository or directory for DevOps configuration files and debt."""
    only_categories: Optional[Set[Category]] = None
    if only:
        only_categories = set()
        for cat_str in only.split(","):
            cat_str = cat_str.strip().lower()
            try:
                only_categories.add(Category(cat_str))
            except ValueError:
                click.echo(f"Warning: Unknown category '{cat_str}' ignored.", err=True)

    fail_on_severity = Severity(fail_on.lower())
    files, findings = execute_scan(path, only_categories=only_categories, ignore_file=ignore_file)

    if output_format == "json":
        json_str = render_json_report(path, files, findings, fail_on_severity)
        click.echo(json_str)
        # Check if threshold violated
        threshold_rank = fail_on_severity.rank
        has_violations = any(f.severity.rank >= threshold_rank for f in findings)
        sys.exit(1 if has_violations else 0)

    if output_format == "sarif":
        sarif_str = render_sarif_report(path, files, findings, fail_on_severity)
        click.echo(sarif_str)
        threshold_rank = fail_on_severity.rank
        has_violations = any(f.severity.rank >= threshold_rank for f in findings)
        sys.exit(1 if has_violations else 0)

    # Terminal output
    exit_code = render_terminal_report(path, files, findings, fail_on_severity)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
