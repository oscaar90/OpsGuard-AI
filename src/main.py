"""Main CLI entry point for OpsGuard-AI."""

import sys
from typing import Annotated

import typer

from src.ai import AIEngine, AIEngineError
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

    # Step 5: Regex check passed - proceed to AI analysis
    typer.secho(
        "✅ Regex Check Passed",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.secho(
        "No hardcoded secrets detected. Proceeding with AI analysis...\n",
        fg=typer.colors.GREEN,
    )

    # Step 6: Initialize AI Engine and run contextual analysis
    try:
        ai_engine = AIEngine()
        typer.secho("Analyzing diff with Gemini AI...", fg=typer.colors.CYAN)
        ai_result = ai_engine.analyze_diff(diff)
    except AIEngineError as e:
        typer.secho(f"AI Engine Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)

    # Step 7: Process AI results
    risk_score = ai_result.get("risk_score", 0)
    verdict = ai_result.get("verdict", "APPROVE")
    issues = ai_result.get("issues", [])

    # Decision logic: BLOCK if verdict is BLOCK or risk_score >= 7
    should_block = verdict == "BLOCK" or risk_score >= 7

    if should_block:
        typer.secho(
            f"\n🚨 AI SECURITY ANALYSIS: BLOCKED (Risk Score: {risk_score}/10)",
            fg=typer.colors.RED,
            bold=True,
        )

        if issues:
            typer.secho("\nIssues Found:", fg=typer.colors.RED, bold=True)
            typer.secho("-" * 60, fg=typer.colors.RED)

            for issue in issues:
                severity = issue.get("severity", "Unknown")
                issue_type = issue.get("type", "Unknown")
                description = issue.get("description", "No description")
                file_name = issue.get("file", "unknown")

                # Color severity
                severity_color = typer.colors.RED
                if severity == "High":
                    severity_color = typer.colors.RED
                elif severity == "Medium":
                    severity_color = typer.colors.YELLOW
                elif severity == "Low":
                    severity_color = typer.colors.CYAN

                typer.secho(
                    f"  [{severity}] ",
                    fg=severity_color,
                    bold=True,
                    nl=False,
                )
                typer.secho(f"({issue_type}) ", fg=typer.colors.WHITE, nl=False)
                typer.secho(f"{description}", fg=typer.colors.WHITE)
                typer.secho(f"           File: {file_name}", fg=typer.colors.BRIGHT_BLACK)

            typer.secho("-" * 60, fg=typer.colors.RED)

        typer.secho(
            "\n⛔ Pipeline blocked by AI analysis. Review the issues above.",
            fg=typer.colors.RED,
            bold=True,
        )
        sys.exit(1)

    # AI analysis passed
    typer.secho(
        f"\n✅ AI Analysis Passed (Risk Score: {risk_score}/10)",
        fg=typer.colors.GREEN,
        bold=True,
    )

    if issues:
        typer.secho("\nMinor issues noted (non-blocking):", fg=typer.colors.YELLOW)
        for issue in issues:
            severity = issue.get("severity", "Unknown")
            description = issue.get("description", "No description")
            typer.secho(f"  [{severity}] {description}", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
