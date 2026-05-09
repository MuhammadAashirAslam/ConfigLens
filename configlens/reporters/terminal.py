"""Terminal reporting with colorized category grouping and summary formatting."""

from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

from configlens import __version__
from configlens.models import Category, DiscoveredFile, Finding, Severity

console = Console(highlight=False)

SEVERITY_COLORS = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "bold orange3",
    Severity.MEDIUM: "bold yellow",
    Severity.LOW: "bold cyan",
}

SEVERITY_BADGES = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH    ",
    Severity.MEDIUM: "MEDIUM  ",
    Severity.LOW: "LOW     ",
}


def render_terminal_report(
    target_path: Path,
    discovered_files: List[DiscoveredFile],
    findings: List[Finding],
    fail_on: Severity,
) -> int:
    """Render human-readable colorized terminal report and return appropriate exit code.

    Returns:
        0 if no findings meet or exceed fail_on threshold; 1 otherwise.
    """
    console.print(f"\n[bold cyan]ConfigLens[/bold cyan] v{__version__} - Scanning [bold]{target_path.resolve()}[/bold]\n")

    if not discovered_files:
        console.print("[yellow]No supported DevOps configuration files discovered.[/yellow]\n")
        return 0

    if not findings:
        console.print(
            f"[bold green]OK All clean![/bold green] Scanned {len(discovered_files)} config file(s) - 0 configuration debt findings detected.\n"
        )
        return 0

    # Group findings by category
    findings_by_category: Dict[Category, List[Finding]] = {}
    for f in findings:
        findings_by_category.setdefault(f.category, []).append(f)

    # Print findings grouped by category
    for cat, cat_findings in findings_by_category.items():
        console.print(f"[bold white]{cat.display_name}[/bold white]")
        console.print("-" * len(cat.display_name))

        for f in cat_findings:
            sev_color = SEVERITY_COLORS.get(f.severity, "white")
            badge = SEVERITY_BADGES.get(f.severity, f.severity.value.upper())

            try:
                rel_file = f.file_path.relative_to(target_path).as_posix()
            except ValueError:
                rel_file = f.file_path.as_posix()

            loc_str = f"{rel_file}:{f.line_number}"
            console.print(f"[{sev_color}]! {badge}[/{sev_color}] {f.title:<34} [dim]{loc_str}[/dim]")
            if f.suggested_fix:
                console.print(f"         [dim]Fix: {f.suggested_fix}[/dim]")

        console.print()

    # Calculate summary counts
    critical_cnt = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    high_cnt = sum(1 for f in findings if f.severity == Severity.HIGH)
    medium_cnt = sum(1 for f in findings if f.severity == Severity.MEDIUM)
    low_cnt = sum(1 for f in findings if f.severity == Severity.LOW)

    summary_text = (
        f"[bold]Summary:[/bold] {len(findings)} finding(s) "
        f"([bold red]{critical_cnt} critical[/bold red], "
        f"[bold orange3]{high_cnt} high[/bold orange3], "
        f"[bold yellow]{medium_cnt} medium[/bold yellow], "
        f"[bold cyan]{low_cnt} low[/bold cyan])"
    )
    console.print(summary_text)

    # Determine exit code based on threshold
    threshold_rank = fail_on.rank
    failing_findings = [f for f in findings if f.severity.rank >= threshold_rank]

    if failing_findings:
        console.print(
            f"[bold red]Exit code: 1[/bold red] (threshold: [bold]{fail_on.value}[/bold] - {len(failing_findings)} finding(s) meet or exceed threshold)\n"
        )
        return 1

    console.print(
        f"[bold green]Exit code: 0[/bold green] (threshold: [bold]{fail_on.value}[/bold] - no findings exceed threshold)\n"
    )
    return 0
