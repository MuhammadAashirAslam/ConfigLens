"""CLI entrypoint for ConfigLens."""

import click
from configlens import __version__


@click.group()
@click.version_option(version=__version__, prog_name="configlens")
def main() -> None:
    """ConfigLens: Static Analysis & Technical Debt Detection for DevOps Configuration."""
    pass


if __name__ == "__main__":
    main()
