"""Main CLI entry point for OpsGuard-AI."""
import sys
import os
import typer
from typing import Annotated
from pathlib import Path

# NOTA DE ARQUITECTURA:
# Mantenemos el Global Scope limpio de imports pesados.
# Solo stdlib y Typer aquí arriba.

app = typer.Typer(
    name="opsguard",
    help="AI-powered DevOps guardian for code review and security analysis.",
    no_args_is_help=True,
    add_completion=False # Desactiva completion para evitar ruido en logs de CI
)

# --- FIX CRÍTICO: CALLBACK EXPLÍCITO ---
@app.callback()
def main_callback():
    """
    OpsGuard AI Security Gate Entrypoint.
    """
    pass

@app.command()
def scan(
    path: Annotated[str, typer.Option(help="Path to the repository to scan.")] = ".",
    config: Annotated[str, typer.Option(help="Path to security policy config.")] = "opsguard.yml",
) -> None:
    """
    Hybrid Security Gate: Regex Shield + AI Brain.
    """
    # --- LAZY IMPORTS START ---
    # Importamos las librerías de negocio DENTRO del comando.
    import pathspec
    from src.ai import AIEngine
    from src.ingest import GitManager
    from src.security import SecurityPolicy
    from src.console_ui import OpsGuardUI
    # --- LAZY IMPORTS END ---

    OpsGuardUI.print_banner()

    # --- HELPER: IGNORE LOGIC ---
    def _load_ignore_spec(root: Path) -> pathspec.PathSpec:
        """Carga patrones de exclusión para reducir ruido y coste de tokens."""
        ignore_path = root / ".opsguardignore"
        lines = []
        if ignore_path.exists():
            with open(ignore_path, "r") as f:
                lines = f.read().splitlines()
        # Siempre ignorar .git y archivos de lock por defecto
        lines.extend([".git/", "*.lock"]) 
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    # 1. Init & Git Context
    try:
        root_path = Path(path)
        policy = SecurityPolicy(config_path=config)
        manager = GitManager(repo_path=str(root_path))
        
        # [NEW] Pre-filtering Stage
        # Optimizamos el payload antes de procesar nada.
        ignore_spec = _load_ignore_spec(root_path)
        
        # Requiere que GitManager tenga un método para listar archivos en staging
        all_staged_files = manager.get_staged_files() 
        
        # Filtramos contra el spec
        target_files = [
            f for f in all_staged_files 
            if not ignore_spec.match_file(f)
        ]

        if not target_files:
            print("✨ No relevant changes detected (filtered by .opsguardignore).")
            raise typer.Exit(code=0)

        # Solo generamos el diff de los archivos que importan
        diff = manager.get_diff(files=target_files)

    except AttributeError:
        typer.secho("❌ API Mismatch: Asegúrate de que GitManager tenga 'get_staged_files()' y 'get_diff(files=...)'.", fg=typer.colors.RED)
        sys.exit(1)
    except Exception as e:
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
        # El diff ya está limpio de basura, optimizando tokens/coste
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