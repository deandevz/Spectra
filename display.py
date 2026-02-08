from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

ROLE_COLORS = {
    "advocate": "green",
    "critic": "red",
    "analyst": "yellow",
}

ROLE_EMOJI = {
    "advocate": "[green]🟢[/green]",
    "critic": "[red]🔴[/red]",
    "analyst": "[yellow]🟡[/yellow]",
}


def display_header():
    console.print(
        Panel(
            "[bold blue]Deep Research Agent[/bold blue]\n"
            "[dim]Debate Roundtable[/dim]",
            border_style="blue",
        )
    )


def display_step(step: str, description: str = ""):
    console.print()
    text = f"[bold cyan]▶ {step}[/bold cyan]"
    if description:
        text += f"  [dim]{description}[/dim]"
    console.print(text)
    console.print("[dim]" + "─" * 60 + "[/dim]")


def display_subtopics(subtopics: list[str]):
    for i, topic in enumerate(subtopics, 1):
        console.print(f"  [cyan]{i}.[/cyan] {topic}")


def display_perspectives(perspectives: list[dict]):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Perspective", style="bold")
    table.add_column("Role")
    table.add_column("Description", max_width=50)

    for p in perspectives:
        color = ROLE_COLORS.get(p["role"], "white")
        table.add_row(
            f"[{color}]{p['name']}[/{color}]",
            p["role"],
            p["system_prompt"][:80] + "..." if len(p["system_prompt"]) > 80 else p["system_prompt"],
        )

    console.print(table)


def display_search_progress(query: str, index: int, total: int):
    console.print(f"  [dim]🔍 [{index}/{total}][/dim] Searching: [italic]{query}[/italic]")


def display_search_done(total_sources: int):
    console.print(f"  [green]✓[/green] {total_sources} sources found and summarized")


def display_debater_search(agent: str, query: str):
    console.print(f"  [dim]🔎 {agent}[/dim] searching: [italic]{query}[/italic]")


def display_debate_argument(agent: str, role: str, text: str, round_num: int):
    color = ROLE_COLORS.get(role, "white")
    emoji = ROLE_EMOJI.get(role, "")
    console.print(
        Panel(
            text,
            title=f"{emoji} {agent} [dim](Round {round_num})[/dim]",
            border_style=color,
            padding=(1, 2),
        )
    )


def display_synthesis(synthesis: dict):
    if synthesis.get("consensus"):
        console.print("\n  [bold green]Consensus:[/bold green]")
        for item in synthesis["consensus"]:
            console.print(f"    [green]•[/green] {item}")

    if synthesis.get("conflicts"):
        console.print("\n  [bold red]Conflicts:[/bold red]")
        for item in synthesis["conflicts"]:
            console.print(f"    [red]•[/red] {item}")

    if synthesis.get("gaps"):
        console.print("\n  [bold yellow]Gaps:[/bold yellow]")
        for item in synthesis["gaps"]:
            console.print(f"    [yellow]•[/yellow] {item}")


def display_more_research(gap_queries: list[str]):
    console.print("\n  [bold yellow]↻ Additional research needed:[/bold yellow]")
    for q in gap_queries:
        console.print(f"    [yellow]→[/yellow] {q}")


def display_evaluation(evaluation: dict):
    scores = evaluation.get("scores", {})
    average = evaluation.get("average", 0.0)
    justifications = evaluation.get("justifications", {})

    table = Table(show_header=True, header_style="bold magenta", title="Report Evaluation")
    table.add_column("Dimension", style="bold")
    table.add_column("Score", justify="center")
    table.add_column("Justification", max_width=60)

    dimension_labels = {
        "coverage": "Coverage",
        "balance": "Balance",
        "citations": "Citations",
        "depth": "Depth",
    }

    for key, label in dimension_labels.items():
        score = scores.get(key, 0)
        color = "green" if score >= 7 else "yellow" if score >= 5 else "red"
        justification = justifications.get(key, "")
        table.add_row(label, f"[{color}]{score}/10[/{color}]", justification)

    console.print()
    console.print(table)

    avg_color = "green" if average >= 7 else "yellow" if average >= 5 else "red"
    console.print(f"\n  [bold]Average:[/bold] [{avg_color}]{average:.1f}/10[/{avg_color}]")

    if average < 7.0:
        console.print("  [yellow]↻ Insufficient quality — resending to Publisher with feedback[/yellow]")
    else:
        console.print("  [green]✓ Report approved![/green]")


def display_final_report_saved(path: str):
    console.print()
    console.print(
        Panel(
            f"[bold green]Report saved at:[/bold green] {path}",
            border_style="green",
        )
    )
