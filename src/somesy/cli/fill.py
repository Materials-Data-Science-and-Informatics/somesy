"""Fill command of somesy."""
import logging
from pathlib import Path
from sys import stdin

import typer
from jinja2 import Environment, FileSystemLoader, FunctionLoader, select_autoescape

from somesy.core.core import discover_input

from ..core.models import SomesyInput
from .util import wrap_exceptions

logger = logging.getLogger("somesy")
app = typer.Typer()


@app.callback(invoke_without_command=True)
@wrap_exceptions
def fill(
    template_file: Path = typer.Option(
        None,
        "--template",
        "-t",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=False,
        help="Path to a Jinja2 template for somesy to fill (default: stdin).",
    ),
    input_file: Path = typer.Option(
        None,
        "--input-file",
        "-i",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path of somesy input file (default: try to infer).",
    ),
    output_file: Path = typer.Option(
        None,
        "--output-file",
        "-o",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=False,
        resolve_path=True,
        help="Path for target file (default: stdout).",
    ),
):
    """Fill a Jinja2 template with somesy project metadata (e.g. list authors in project docs)."""
    somesy_input = SomesyInput.from_input_file(discover_input(input_file))
    if template_file:
        env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
        template = env.get_template(str(template_file))
    else:
        env = Environment(
            loader=FunctionLoader(lambda _: stdin.read()),
            autoescape=select_autoescape(),
        )
        template = env.get_template("")
    result = template.render(project=somesy_input.project)
    if not output_file:
        print(result)
    else:
        with open(output_file, "w") as f:
            f.write(result)
