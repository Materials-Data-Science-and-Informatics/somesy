"""Sync command for somesy."""
import traceback
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console

from somesy.commands import sync_from_pyproject

app = typer.Typer()
err_console = Console(stderr=True)


@app.command()
def sync(
    cff_path: Optional[Path] = typer.Option(
        default=Path("CITATION.cff"),
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="CITATION.cff path",
    ),
    create_cff: bool = typer.Option(
        default=True,
        help="Create CITATION.cff if it does not exist",
    ),
    pyproject_path: Optional[Path] = typer.Option(
        default=Path("pyproject.toml"),
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="pyproject.toml path",
    ),
    create_pyproject: bool = typer.Option(
        default=True,
        help="Create pyproject.toml if it does not exist",
    ),
    verbose: bool = typer.Option(
        default=True,
        help="Verbose output",
    ),
):
    """Sync project metadata file with metadata files."""
    try:
        print("[bold green]Syncing:[/bold green]")
        print(f"  - [italic]Pyproject.toml[/italic] [grey]({pyproject_path})[/grey]")
        if cff_path:
            print(f"  - [italic]CITATION.cff[/italic] [grey]({cff_path})[/grey]")
        sync_from_pyproject(
            pyproject_path=Path(pyproject_path),
            cff_path=Path(cff_path),
            create_cff=create_cff,
            create_pyproject=create_pyproject,
            dump=True,
        )
        print("[bold green]Done.[/bold green]")
    except Exception as e:
        print(f"[bold red]Error: {e}[/bold red]")
        if verbose:
            print(f"[red]{traceback.format_exc()}[/red]")
