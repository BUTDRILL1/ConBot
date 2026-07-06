from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import questionary

console = Console()

def print_banner():
    banner_text = Text()
    banner_text.append("             ConBot v1.0                \n", style="bold cyan")
    banner_text.append("  Convert anything to anything, fast    \n\n", style="cyan")
    banner_text.append("        — Maintained by github/BUTDRILL1", style="dim green")
    
    panel = Panel(
        banner_text,
        style="blue",
        expand=False,
    )
    console.print(panel)
    console.print("ConBot converts files in your CURRENT directory only.")
    console.print("Navigate with ↑↓, select with Enter, go back with Esc, quit with Ctrl+C.\n")

def print_success(msg: str):
    console.print(f"[bold green]✓[/bold green] {msg}")

def print_error(msg: str):
    console.print(f"[bold red]✗[/bold red] {msg}")

def print_warning(msg: str):
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")

def prompt_warning(msg: str, choices: list[str]) -> str | None:
    print_warning(msg)
    try:
        return questionary.select("", choices=choices).unsafe_ask()
    except KeyboardInterrupt:
        return None

def spinner(text: str):
    return console.status(f"[cyan]{text}[/cyan]", spinner="dots")
