from dotenv import load_dotenv

load_dotenv()

from display import console, display_header
from graph import build_graph


def main():
    display_header()
    app = build_graph()

    while True:
        console.print()
        try:
            query = console.input("[bold blue]Research query >[/bold blue] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/dim]")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            console.print("[dim]Bye![/dim]")
            break

        try:
            console.print(f"\n[bold]Researching:[/bold] {query}\n")

            # Stream node-by-node for real-time display
            for update in app.stream(
                {"query": query},
                stream_mode="updates",
            ):
                # Each node's display is handled internally
                pass

            console.print("\n[bold green]✓ Research completed![/bold green]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Research cancelled.[/yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Erro:[/bold red] {e}")


if __name__ == "__main__":
    main()
