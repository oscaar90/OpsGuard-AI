from typing import Annotated

import typer

from src.ingest import GitIngestError, GitManager

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
) -> None:
    """Scan the repository and display the git diff."""
    try:
        manager = GitManager(repo_path=path)
        diff = manager.get_diff()
        if diff:
            print(diff)
        else:
            print("No changes detected.")
    except GitIngestError as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
