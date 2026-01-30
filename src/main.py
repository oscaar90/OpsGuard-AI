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
    add_completion=False
)

@app.callback()
def main_callback():
    """OpsGuard AI Security Gate Entrypoint."""
    pass

@app.command()
def scan(
    path: Annotated[str, typer.Option(help="Path to the repository to scan.")] = ".",
    config: Annotated[str, typer.Option(help="Path to security policy config.")] = "opsguard.yml",
) -> None:
    """
    Hybrid Security Gate: Regex Shield + AI Brain.
    """
    # --- LAZY IMPORTS ---
    import pathspec
    from src.ai import AIEngine
    from src.ingest import GitManager
    from src.security import SecurityPolicy
    from src.console_ui import OpsGuardUI

    OpsGuardUI.print_banner()

    def _load_ignore_spec(root: Path) -> pathspec.PathSpec:
        """Carga patrones de exclusión."""
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
        
        target_files = [
            f for f in all_staged_files 
            if not ignore_spec.match_file(f)
        ]

        if not target_files:
            print("✨ No relevant changes detected (filtered by .opsguardignore).")
            # Esto lanza una excepción 'Exit' que debemos dejar pasar
            raise typer.Exit(code=0)

        diff = manager.get_diff(files=target_files)

    # --- FIX 1: Graceful Exit Signal ---
    except typer.Exit:
        # Re-lanzamos la señal de salida limpia para que Typer termine con código 0.
        raise 

    except AttributeError:
        typer.secho("❌ API Mismatch: Asegúrate de que GitManager tenga 'get_staged_files()'.", fg=typer.colors.RED)
        sys.exit(1)

    # --- FIX 2: Catch Generic Exceptions & SKIP_SCAN Signal ---
    except Exception as e:
        # Si ingest.py lanza SKIP_SCAN (ej. borrado de rama), salimos en verde.
        if "SKIP_SCAN" in str(e):
            print(f"⏭️  {e}")
            raise typer.Exit(code=0)
            
        typer.secho(f"❌ Init Error: {e}", fg=typer.colors.RED)
        sys.exit(1)

    if not diff.strip():
        print("✨ Empty diff content.")
        raise typer.Exit(code=0)

    # 2. FASE 1: Deterministic Shield (Regex)
    violations = policy.scan_diff(diff)

    if violations:
        formatted_findings = [{"file": "Diff", "line": "?", "type": v} for v in violations]
        OpsGuardUI.print_regex_findings(formatted_findings)
        OpsGuardUI.print_block_message()
        sys.exit(1)

    OpsGuardUI.print_regex_findings([]) 

    # 3. FASE 2: Semantic Brain (AI Analysis)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        typer.secho("⚠️ Missing OPENROUTER_API_KEY. Skipping AI.", fg=typer.colors.YELLOW)
        return

    try:
        ai_engine = AIEngine()
        ai_result = ai_engine.analyze_diff(diff)
    except Exception as e:
        typer.secho(f"❌ AI Engine Error: {e}", fg=typer.colors.RED)
        sys.exit(1)

    # 4. Reporte
    OpsGuardUI.print_ai_analysis(ai_result)

    risk_score = ai_result.get("risk_score", 0)
    verdict = ai_result.get("verdict", "APPROVE")
    
    if verdict == "BLOCK" or risk_score >= 7:
        OpsGuardUI.print_block_message()
        sys.exit(1)
    else:
        OpsGuardUI.print_success_message()

if __name__ == "__main__":
    app(prog_name="opsguard")