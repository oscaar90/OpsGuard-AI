from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme

# Definimos un tema corporativo/hacker
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "title": "bold white on blue",
})

console = Console(theme=custom_theme)

class OpsGuardUI:
    @staticmethod
    def print_banner():
        console.print(Panel.fit(
            "[bold white]🛡️ OpsGuard-AI[/bold white]\n[cyan]Security Gate Active[/cyan]",
            border_style="blue"
        ))

    @staticmethod
    def print_regex_findings(findings: list):
        if not findings:
            console.print("[success]✅ No static credential patterns found.[/success]")
            return

        table = Table(title="[danger]🚨 STATIC ANALYSIS FAILURES[/danger]", show_header=True, header_style="bold red")
        table.add_column("File", style="cyan")
        table.add_column("Line", justify="right")
        table.add_column("Secret Type", style="yellow")
        
        for f in findings:
            # Asumimos que finding es un dict u objeto con estos campos
            table.add_row(f['file'], str(f['line']), f['type'])
            
        console.print(table)

    @staticmethod
    def print_ai_analysis(analysis: dict):
        """Renderiza el JSON de la IA de forma bonita"""
        risk_score = analysis.get("risk_score", 0)
        verdict = analysis.get("verdict", "UNKNOWN")
        
        # Color del panel según el riesgo
        color = "green"
        if risk_score >= 5: color = "yellow"
        if risk_score >= 7: color = "red"

        content = f"""
        [bold]🤖 AI Semantic Verdict:[/bold] [{color}]{verdict}[/{color}]
        [bold]🔥 Risk Score:[/bold] {risk_score}/10
        
        [bold]📝 Explanation:[/bold]
        {analysis.get('explanation', 'No explanation provided.')}
        """
        
        console.print(Panel(content, title="🧠 AI Context Analysis", border_style=color))

    @staticmethod
    def print_block_message():
        console.print("\n[bold white on red] ⛔ PIPELINE BLOCKED: SECURITY VIOLATION DETECTED [/bold white on red]\n")

    @staticmethod
    def print_success_message():
        console.print("\n[bold white on green] ✅ PIPELINE APPROVED: CODE IS CLEAN [/bold white on green]\n")