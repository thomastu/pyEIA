"""
Beautiful CLI browser for exploring the EIA API.

This provides an interactive terminal interface for discovering
datasets, exploring facets, and fetching data from the EIA API.
"""

import os
import sys
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich import box

from eia import EIAClient
from eia.v2.exceptions import EIAError

console = Console()


def get_api_key() -> str:
    """Get API key from environment or prompt user."""
    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        console.print(
            "\n[yellow]No API key found in EIA_API_KEY environment variable.[/yellow]"
        )
        console.print(
            "Get your free API key at: [link]https://www.eia.gov/opendata/register.php[/link]\n"
        )
        api_key = Prompt.ask("Enter your EIA API key", password=True)

    return api_key


def display_welcome() -> None:
    """Display welcome banner."""
    welcome = """
    # 🔌 pyEIA API Browser

    Interactive explorer for the U.S. Energy Information Administration API

    **Commands:**
    - Type route numbers to navigate
    - Type 'back' to go back
    - Type 'facets' to view available filters
    - Type 'data' to fetch data
    - Type 'quit' or 'exit' to exit
    """
    console.print(Panel(Markdown(welcome), border_style="blue", box=box.DOUBLE))


def display_routes(routes: list[dict[str, Any]], title: str = "Available Routes") -> None:
    """Display routes in a beautiful table."""
    table = Table(
        title=title, box=box.ROUNDED, header_style="bold magenta", show_lines=True
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    for idx, route in enumerate(routes, 1):
        table.add_row(
            str(idx),
            route.get("id", ""),
            route.get("name", ""),
            route.get("description", "")[:80] + "..." if route.get("description", "") and len(route.get("description", "")) > 80 else route.get("description", ""),
        )

    console.print(table)


def display_facets(facets: list[dict[str, Any]], title: str = "Available Facets") -> None:
    """Display facets in a beautiful table."""
    table = Table(
        title=title, box=box.ROUNDED, header_style="bold magenta", show_lines=False
    )

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Alias", style="dim")

    for facet in facets:
        table.add_row(
            facet.get("id", ""),
            facet.get("name", ""),
            facet.get("alias", ""),
        )

    console.print(table)


def display_data(data: list[dict[str, Any]], total: int, title: str = "Data") -> None:
    """Display data in a beautiful table."""
    if not data:
        console.print("[yellow]No data available[/yellow]")
        return

    # Dynamically create columns based on first record
    table = Table(
        title=f"{title} (showing {len(data)} of {total} records)",
        box=box.SIMPLE,
        header_style="bold cyan",
    )

    # Add columns based on keys in first record
    if data:
        for key in data[0].keys():
            table.add_column(key, style="white")

        # Add rows (limit to first 50 for display)
        for record in data[:50]:
            table.add_row(*[str(record.get(key, "")) for key in data[0].keys()])

    console.print(table)

    if len(data) > 50:
        console.print(f"\n[dim]... and {len(data) - 50} more records[/dim]")


def explore_route(client: EIAClient, route: str = "") -> None:
    """Interactively explore a route."""
    route_path: list[str] = [r for r in route.split("/") if r]

    while True:
        # Build current route
        current_route = "/".join(route_path) if route_path else ""

        # Fetch route metadata
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description=f"Fetching data for: {current_route or 'root'}...",
                total=None,
            )
            try:
                response = client.get_route(current_route)
            except EIAError as e:
                console.print(f"[red]Error: {e}[/red]")
                return

        # Display current path
        if route_path:
            path_display = " → ".join(route_path)
            console.print(
                f"\n[bold blue]Current Path:[/bold blue] {path_display}\n",
            )
        else:
            console.print("\n[bold blue]EIA API Root[/bold blue]\n")

        # Display route information
        route_info = response["response"]

        if route_info.get("description"):
            console.print(
                Panel(
                    route_info["description"],
                    title="Description",
                    border_style="green",
                )
            )

        # Display child routes if available
        child_routes = route_info.get("routes", [])
        if child_routes:
            display_routes(child_routes, "Child Routes")

        # Show available actions
        console.print("\n[bold cyan]Actions:[/bold cyan]")
        actions_table = Table(box=None, show_header=False, padding=(0, 2))
        actions_table.add_row(
            "[cyan]1-N[/cyan]", "Navigate to route by number"
        )
        if route_path:
            actions_table.add_row("[cyan]back[/cyan]", "Go back one level")
        if route_info.get("facets"):
            actions_table.add_row(
                "[cyan]facets[/cyan]", "View available filters/dimensions"
            )
        if route_info.get("frequency"):
            actions_table.add_row("[cyan]data[/cyan]", "Fetch data from this route")
        actions_table.add_row("[cyan]quit/exit[/cyan]", "Exit browser")

        console.print(actions_table)
        console.print()

        # Get user input
        action = Prompt.ask("[bold]Choose action[/bold]").lower().strip()

        # Handle actions
        if action in ("quit", "exit", "q"):
            break
        elif action == "back" and route_path:
            route_path.pop()
        elif action == "facets" and route_info.get("facets"):
            explore_facets(client, current_route, route_info["facets"])
        elif action == "data" and route_info.get("frequency"):
            fetch_data_interactive(client, current_route, route_info)
        elif action.isdigit():
            idx = int(action) - 1
            if 0 <= idx < len(child_routes):
                route_path.append(child_routes[idx]["id"])
            else:
                console.print("[red]Invalid route number[/red]")
        else:
            console.print("[red]Invalid action[/red]")


def explore_facets(client: EIAClient, route: str, facet_names: list[str]) -> None:
    """Explore facets for a route."""
    console.print(
        f"\n[bold blue]Facets for: {route}[/bold blue]\n"
    )

    # Show available facets
    facets_table = Table(
        title="Available Facets",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    facets_table.add_column("#", style="dim", width=4)
    facets_table.add_column("Facet ID", style="cyan")

    for idx, facet_name in enumerate(facet_names, 1):
        facets_table.add_row(str(idx), facet_name)

    console.print(facets_table)

    # Prompt for facet to explore
    choice = Prompt.ask("\nSelect facet number (or 'back' to return)", default="back")

    if choice.lower() == "back":
        return

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(facet_names):
            facet_name = facet_names[idx]

            # Fetch facet values
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(
                    description=f"Fetching values for {facet_name}...", total=None
                )
                try:
                    response = client.get_facet(route, facet_name)
                except EIAError as e:
                    console.print(f"[red]Error: {e}[/red]")
                    return

            facet_items = response["response"]["facets"]
            display_facets(facet_items, f"Values for: {facet_name}")

            Prompt.ask("\nPress Enter to continue")


def fetch_data_interactive(
    client: EIAClient, route: str, route_info: dict[str, Any]
) -> None:
    """Interactively fetch data from a route."""
    console.print(f"\n[bold blue]Fetch Data from: {route}[/bold blue]\n")

    # Show available data columns
    # API returns data in two formats:
    # - dict: {"column_name": {"alias": "...", ...}}
    # - list: ["column1", "column2", ...]
    data_cols = route_info.get("data", {})
    column_names: list[str] = []

    if data_cols:
        console.print("[bold]Available data columns:[/bold]")
        if isinstance(data_cols, dict):
            # Dictionary format with metadata
            for col_name, col_info in data_cols.items():
                if isinstance(col_info, dict):
                    alias = col_info.get("alias", col_name)
                    console.print(f"  • {col_name}: {alias}")
                else:
                    console.print(f"  • {col_name}")
                column_names.append(col_name)
        elif isinstance(data_cols, list):
            # List format (just column names)
            for col_name in data_cols:
                console.print(f"  • {col_name}")
                column_names.append(col_name)
        console.print()

    # Prompt for data columns
    data_input = Prompt.ask(
        "Data columns (comma-separated, or 'all')",
        default="all",
    )

    if data_input.lower() == "all":
        data_columns = column_names if column_names else None
    else:
        data_columns = [c.strip() for c in data_input.split(",")]

    # Prompt for frequency
    frequencies = route_info.get("frequency", [])
    if frequencies:
        # Ensure frequencies is a list
        if not isinstance(frequencies, list):
            frequencies = [frequencies]
        console.print(f"\n[bold]Available frequencies:[/bold] {', '.join(frequencies)}")
        frequency = Prompt.ask("Frequency", choices=frequencies, default=frequencies[0])
    else:
        frequency = None

    # Prompt for filters
    facets_dict = {}
    facets = route_info.get("facets", [])
    if facets:
        # Ensure facets is a list
        if not isinstance(facets, list):
            facets = [facets]
        use_filters = Confirm.ask("\nApply filters?", default=False)
        if use_filters:
            console.print("[dim]Enter filter values (e.g., 'CA,NY' for states)[/dim]")
            for facet in facets:
                values = Prompt.ask(f"  {facet} (leave empty to skip)", default="")
                if values:
                    facets_dict[facet] = [v.strip() for v in values.split(",")]

    # Prompt for row limit
    max_rows = Prompt.ask("Maximum rows to fetch", default="100")
    try:
        max_rows_int = int(max_rows)
    except ValueError:
        max_rows_int = 100

    # Fetch data
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Fetching data...", total=None)
        try:
            response = client.get_data(
                route=route,
                data=data_columns,
                frequency=frequency,
                facets=facets_dict if facets_dict else None,
                length=min(max_rows_int, 5000),
            )
        except EIAError as e:
            console.print(f"[red]Error: {e}[/red]")
            Prompt.ask("\nPress Enter to continue")
            return
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            console.print("[dim]This may indicate an API issue or invalid parameters.[/dim]")
            Prompt.ask("\nPress Enter to continue")
            return

    # Display data
    data = response["response"]["data"]
    total = response["response"]["total"]
    display_data(data, total)

    # Ask if user wants to export
    if data:
        export = Confirm.ask("\nExport to CSV?", default=False)
        if export:
            filename = Prompt.ask("Filename", default="eia_data.csv")
            try:
                import csv
                with open(filename, "w", newline="") as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                console.print(f"[green]✓ Data exported to {filename}[/green]")
            except Exception as e:
                console.print(f"[red]Export failed: {e}[/red]")

    Prompt.ask("\nPress Enter to continue")


def main() -> None:
    """Main entry point for the browser CLI."""
    try:
        display_welcome()

        # Get API key
        api_key = get_api_key()

        # Create client
        client = EIAClient(api_key=api_key)

        # Test connection
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Testing API connection...", total=None)
            try:
                client.get_route()
            except EIAError as e:
                console.print(f"\n[red]Failed to connect to EIA API: {e}[/red]")
                console.print(
                    "[yellow]Please check your API key and internet connection.[/yellow]"
                )
                sys.exit(1)

        console.print("[green]✓ Connected successfully![/green]\n")

        # Start exploring
        explore_route(client)

        console.print("\n[bold green]Thank you for using pyEIA Browser![/bold green]")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
