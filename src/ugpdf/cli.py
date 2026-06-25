"""CLI entry point for ugpdf."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .pdf import generate_pdf
from .search import TabResult, search
from .select import pick_best

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="1.0.0", prog_name="ugpdf")
@click.argument("query", nargs=-1, required=True)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default=None,
    help="Output PDF file path. Auto-generated from artist/title if omitted.",
)
@click.option(
    "-t", "--type",
    "tab_type",
    type=click.Choice(["Chords", "Tab", "Guitar Pro", "Bass"], case_sensitive=False),
    default=None,
    help="Filter results by tab type.",
)
@click.option(
    "--list", "list_versions",
    is_flag=True,
    default=False,
    help="Show all available versions in a table.",
)
@click.option(
    "--pick",
    type=int,
    default=None,
    help="Select version N from the list (use with --list).",
)
def main(
    query: tuple[str, ...],
    output: str | None,
    tab_type: str | None,
    list_versions: bool,
    pick: int | None,
) -> None:
    """Download Ultimate Guitar tabs as clean PDF files.

    Searches Ultimate Guitar, auto-selects the best community version
    (highest votes, non-official), and saves it as a print-ready PDF.

    \b
    Examples:
        ugpdf teen spirit nirvana
        ugpdf "hotel california" --type Chords
        ugpdf wonderwall oasis -o wonderwall.pdf
        ugpdf "stairway to heaven" --list
        ugpdf "stairway to heaven" --list --pick 2
    """
    search_query = " ".join(query)
    asyncio.run(_run(search_query, output, tab_type, list_versions, pick))


async def _run(
    search_query: str,
    output: str | None,
    tab_type: str | None,
    list_versions: bool,
    pick: int | None,
) -> None:
    """Async main flow."""

    # --- Step 1: Search ---
    console.print(f"\n[bold blue]🔍 Searching:[/] {search_query}")

    try:
        results = await search(search_query, tab_type=tab_type or "")
    except Exception as e:
        console.print(f"[bold red]✗[/] Search failed: {e}")
        sys.exit(1)

    if not results:
        console.print("[bold red]✗[/] No results found.")
        sys.exit(1)

    # --- Step 2: Select ---
    if list_versions:
        _show_versions(results)
        if pick is None:
            return
        if pick < 1 or pick > len(results):
            console.print(f"[bold red]✗[/] Invalid pick. Choose 1-{len(results)}.")
            sys.exit(1)
        selected = results[pick - 1]
    else:
        selected = pick_best(results)
        if selected is None:
            console.print("[bold red]✗[/] No suitable (non-official) version found.")
            sys.exit(1)

    # Show selection
    official_tag = " [dim](official)[/]" if selected.is_official else ""
    console.print(
        f"[bold green]✓[/] Selected: [bold]{selected.artist} – {selected.title}[/]"
        f"{official_tag}"
    )
    console.print(
        f"  [dim]Type:[/] {selected.type}  "
        f"[dim]Rating:[/] ★{selected.rating:.1f}  "
        f"[dim]Votes:[/] {selected.display_votes}"
    )
    console.print(f"  [dim]URL:[/] {selected.url}")

    # --- Step 3: Generate PDF ---
    console.print("\n[bold blue]🖨️  Generating PDF...[/]")

    output_path = Path(output) if output else None

    try:
        result_path = await generate_pdf(
            selected.url,
            artist=selected.artist,
            title=selected.title,
            output_path=output_path,
        )
    except Exception as e:
        console.print(f"[bold red]✗[/] PDF generation failed: {e}")
        sys.exit(1)

    console.print(f"[bold green]✅ Saved:[/] {result_path}\n")


def _show_versions(results: list[TabResult]) -> None:
    """Display a numbered table of all versions."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Artist")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Rating", justify="right")
    table.add_column("Votes", justify="right")
    table.add_column("", width=10)  # official badge

    for i, r in enumerate(results, 1):
        badge = "[yellow]official[/]" if r.is_official else ""
        table.add_row(
            str(i),
            r.artist,
            r.title,
            r.type,
            f"★{r.rating:.1f}",
            r.display_votes,
            badge,
        )

    console.print()
    console.print(table)
    console.print("\n[dim]Tip: use --pick N to select a version[/]\n")


if __name__ == "__main__":
    main()
