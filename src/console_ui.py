from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


class OpsGuardUI:
    @staticmethod
    def print_banner():
        console.print(
            Panel.fit(
                "[bold cyan]🛡️ OpsGuard-AI[/bold cyan]\n[dim]Security Gate Active[/dim]",
                border_style="cyan",
            )
        )

    @staticmethod
    def print_regex_findings(findings: list):
        if not findings:
            console.print("✅ [green]No static credential patterns found.[/green]")
            return

        console.print(
            f"\n[bold red]🚨 DETECTED {len(findings)} STATIC VIOLATIONS:[/bold red]"
        )
        table = Table(
            show_header=True, header_style="bold white on red", box=box.ROUNDED
        )
        table.add_column("Type")
        table.add_column("File")

        for f in findings:
            table.add_row(f.get("type"), f.get("file"))

        console.print(table)

    @staticmethod
    def print_ai_analysis(result: dict):
        console.print(
            "\n[bold blue]╭─────────────────────────── 🧠 AI Context Analysis ───────────────────────────╮[/bold blue]"
        )

        verdict = result.get("verdict", "UNKNOWN")
        score = result.get("risk_score", 0)
        explanation = result.get("explanation", "No details.")
        findings = result.get("findings", [])

        # Verdict traffic light
        if verdict == "APPROVE":
            v_style = "bold green"
        else:
            v_style = "bold white on red"

        console.print(f"│         🤖 Verdict: [{v_style}] {verdict} [/{v_style}]")
        console.print(f"│         🔥 Risk Score: {score}/10")
        console.print(f"│         📝 Summary: [italic]{explanation}[/italic]")
        console.print(
            "╰──────────────────────────────────────────────────────────────────────────────╯"
        )

        if findings:
            console.print("\n[bold red]🕵️‍♂️  AI FORENSIC FINDINGS:[/bold red]")

            table = Table(
                show_header=True,
                header_style="bold white on red",
                border_style="red",
                box=box.HEAVY_HEAD,
            )
            table.add_column("Sev", justify="center", width=8)
            table.add_column("File", style="cyan")
            table.add_column("Line", style="yellow")
            table.add_column("Issue", style="white")

            for finding in findings:
                sev = finding.get("severity", "UNK")
                # Critical severity highlighting
                sev_color = "red" if sev in ["CRITICAL", "HIGH"] else "yellow"

                table.add_row(
                    f"[{sev_color}]{sev}[/{sev_color}]",
                    finding.get("file", "-"),
                    str(finding.get("line", "?")),
                    finding.get("issue", "No description"),
                )

            console.print(table)

    @staticmethod
    def print_block_message():
        console.print(
            "\n[bold white on red] ⛔ PIPELINE BLOCKED: SECURITY VIOLATION DETECTED [/bold white on red]"
        )

    @staticmethod
    def print_success_message():
        console.print(
            "\n[bold black on green] ✅ PIPELINE APPROVED: CODE IS SECURE [/bold black on green]"
        )
