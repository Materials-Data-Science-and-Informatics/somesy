"""Fill command of somesy."""
import logging
from pathlib import Path
from sys import stdin

import typer
from jinja2 import Environment, FunctionLoader, select_autoescape

from .util import resolved_somesy_input, wrap_exceptions

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
    somesy_input = resolved_somesy_input(input_file=input_file)

    if template_file:
        logger.debug(f"Reading Jinja2 template from '{template_file}'.")
        with open(template_file, "r") as f:
            template_str = f.read()
    else:
        logger.debug("Reading Jinja2 template from stdin.")
        template_str = stdin.read()

    result = (
        Environment(
            loader=FunctionLoader(lambda _: template_str),
            autoescape=select_autoescape(),
        )
        .get_template("")
        .render(project=somesy_input.project)
    )

    if output_file:
        logger.debug(f"Writing result to '{output_file}'.")
        with open(output_file, "w") as f:
            f.write(result)
    else:
        logger.debug("Writing result to stdout.")
        print(result)
