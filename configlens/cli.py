"""CLI entrypoint and commands for ConfigLens."""

import json
from pathlib import Path
from typing import Optional, Set
import click
from rich.console import Console
from rich.table import Table

from configlens import __version__
from configlens.discovery import discover_files
from configlens.models import Category

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="configlens")
def main() -> None:
    """ConfigLens: Static Analysis & Technical Debt Detection for DevOps Configuration."""
    pass


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
    type=click.Choice(["terminal", "json"], case_sensitive=False),
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
                console.print(f"[yellow]Warning:[/yellow] Unknown category '{cat_str}' ignored.")

    files = discover_files(path, only=only_categories, ignore_file=ignore_file)

    if output_format == "json":
        report = {
            "version": __version__,
            "target": str(path.resolve()),
            "discovered_files_count": len(files),
            "files": [f.to_dict() for f in files],
            "findings": [],
            "summary": {
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }
        click.echo(json.dumps(report, indent=2))
        return

    # Terminal output
    console.print(f"\n[bold cyan]ConfigLens[/bold cyan] v{__version__} — Scanning [bold]{path.resolve()}[/bold]\n")

    if not files:
        console.print("[yellow]No supported DevOps configuration files discovered.[/yellow]\n")
        return

    table = Table(title="Discovered DevOps Configurations", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan", width=20)
    table.add_column("File Path", style="green")
    table.add_column("Size", justify="right", style="dim")

    # Group files by category
    category_counts: dict[str, int] = {}
    for f in files:
        cat_name = f.category.display_name
        category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        size_str = f"{f.size_bytes} B" if f.size_bytes < 1024 else f"{f.size_bytes / 1024:.1f} KB"
        table.add_row(cat_name, f.relative_path.as_posix(), size_str)

    console.print(table)
    console.print(f"\n[bold green]Summary:[/bold green] Discovered {len(files)} config files across {len(category_counts)} categories (0 findings).\n")


if __name__ == "__main__":
    main()
