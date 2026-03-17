"""Main CLI entry point for OpsGuard-AI."""

import sys
import os
import typer
from typing import Annotated
from pathlib import Path

app = typer.Typer(
    name="opsguard",
    help="AI-powered DevOps guardian for code review and security analysis.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main_callback():
    """OpsGuard AI Security Gate Entrypoint."""
    pass


@app.command()
def scan(
    path: Annotated[str, typer.Option(help="Path to the repository to scan.")] = ".",
    config: Annotated[
        str, typer.Option(help="Path to security policy config.")
    ] = "opsguard.yml",
) -> None:
    """
    Hybrid Security Gate: Regex Shield + AI Brain.
    """
    # --- LAZY IMPORTS ---
    import pathspec
    from src.ai import AIEngine
    from src.ingest import GitManager, SkipScanSignal
    from src.security import SecurityPolicy
    from src.console_ui import OpsGuardUI

    OpsGuardUI.print_banner()

    def _load_ignore_spec(root: Path) -> pathspec.PathSpec:
        """Load exclusion patterns from .opsguardignore."""
        ignore_path = root / ".opsguardignore"
        lines = []
        if ignore_path.exists():
            with open(ignore_path, "r") as f:
                lines = f.read().splitlines()
        lines.extend([".git/", "*.lock"])
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    # 1. Init & Git Context
    try:
        root_path = Path(path)
        policy = SecurityPolicy(config_path=config)
        manager = GitManager(repo_path=str(root_path))

        # Pre-filtering Stage
        ignore_spec = _load_ignore_spec(root_path)

        # [SECURITY AUDIT NOTE]
        # Implementation of Standard Ignore Mechanism.
        # This uses 'pathspec' to filter non-code artifacts.
        all_staged_files = manager.get_staged_files()

        target_files = [f for f in all_staged_files if not ignore_spec.match_file(f)]

        if not target_files:
            print("✨ No relevant changes detected (filtered by .opsguardignore).")
            # typer.Exit is intentional - let it propagate
            raise typer.Exit(code=0)

        diff = manager.get_diff(files=target_files)

    except typer.Exit:
        raise

    except SkipScanSignal as e:
        print(f"⏭️  {e}")
        raise typer.Exit(code=0)

    except AttributeError:
        typer.secho(
            "❌ API Mismatch: GitManager is missing the 'get_staged_files()' method.",
            fg=typer.colors.RED,
        )
        sys.exit(1)

    except Exception as e:
        typer.secho(f"❌ Init Error: {e}", fg=typer.colors.RED)
        sys.exit(1)

    if not diff.strip():
        print("✨ Empty diff content.")
        raise typer.Exit(code=0)

    # 2. Gate 1: Deterministic Shield (Regex)
    violations = policy.scan_diff(diff)

    if violations:
        formatted_findings = [
            {"file": "Diff", "line": "?", "type": v} for v in violations
        ]
        OpsGuardUI.print_regex_findings(formatted_findings)
        OpsGuardUI.print_block_message()
        sys.exit(1)

    OpsGuardUI.print_regex_findings([])

    # 3. Gate 2: Semantic Brain (AI Analysis)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        typer.secho(
            "⚠️ Missing OPENROUTER_API_KEY. Skipping AI.", fg=typer.colors.YELLOW
        )
        return

    try:
        ai_engine = AIEngine()
        ai_result = ai_engine.analyze_diff(diff)
    except Exception as e:
        typer.secho(f"❌ AI Engine Error: {e}", fg=typer.colors.RED)
        sys.exit(1)

    # 4. Report
    OpsGuardUI.print_ai_analysis(ai_result)

    risk_score = ai_result.get("risk_score", 0)
    verdict = ai_result.get("verdict", "APPROVE")
    risk_threshold = int(os.getenv("OPSGUARD_RISK_THRESHOLD", "7"))

    if verdict == "BLOCK" or risk_score >= risk_threshold:
        OpsGuardUI.print_block_message()
        sys.exit(1)
    else:
        OpsGuardUI.print_success_message()


if __name__ == "__main__":
    app(prog_name="opsguard")
