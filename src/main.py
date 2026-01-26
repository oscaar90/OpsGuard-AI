"""Main CLI entry point for OpsGuard-AI."""

import sys
from typing import Annotated

import typer

from src.ingest import GitIngestError, GitManager
from src.security import SecurityPolicy, SecurityPolicyError

app = typer.Typer(
    name="opsguard",
    help="AI-powered DevOps guardian for code review and security analysis.",
)


@app.command()
def run(
    path: Annotated[str, typer.Option(help="Path to the repository to analyze.")] = ".",
) -> None:
    """Run OpsGuard analysis on the specified path."""
    print("OpsGuard Initialized")


@app.command()
def scan(
    path: Annotated[str, typer.Option(help="Path to the repository to scan.")] = ".",
    config: Annotated[str, typer.Option(help="Path to security policy config.")] = "opsguard.yml",
) -> None:
    """Scan the repository for security violations in the git diff.

    This command implements the Local Gatekeeper pattern (ADR-0001):
    1. Fetches the git diff (local or CI mode)
    2. Scans for hardcoded secrets using deterministic rules
    3. Hard fails if violations are found (before any LLM analysis)
    """
    # Step 1: Initialize security policy
    try:
        policy = SecurityPolicy(config_path=config)
    except SecurityPolicyError as e:
        typer.secho(f"Security Policy Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)

    # Step 2: Get git diff
    try:
        manager = GitManager(repo_path=path)
        diff = manager.get_diff()
    except GitIngestError as e:
        typer.secho(f"Git Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)

    if not diff:
        typer.secho("No changes detected.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    # Step 3: Run security scan (Local Gatekeeper)
    violations = policy.scan_diff(diff)

    # Step 4: Handle results
    if violations:
        typer.secho(
            "\n🚨 SECURITY VIOLATIONS DETECTED (Hard Fail)",
            fg=typer.colors.RED,
            bold=True,
        )
        typer.secho(
            "The following secrets were found in added lines:\n",
            fg=typer.colors.RED,
        )
        for violation in violations:
            typer.secho(f"  ✗ {violation}", fg=typer.colors.RED)

        typer.secho(
            "\n⛔ Pipeline blocked. Remove secrets before proceeding.",
            fg=typer.colors.RED,
            bold=True,
        )
        typer.secho(
            "LLM analysis was NOT performed to prevent data leakage.",
            fg=typer.colors.YELLOW,
        )
        sys.exit(1)

    # All clear - proceed
    typer.secho(
        "✅ Security Check Passed",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.secho(
        "No hardcoded secrets detected. Safe to proceed with LLM analysis.",
        fg=typer.colors.GREEN,
    )


if __name__ == "__main__":
    app()
