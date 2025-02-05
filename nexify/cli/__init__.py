import logging
from typing import Annotated

try:
    import typer
except ImportError:  # pragma: no cover
    message = 'To use the nexify command, please install "nexify[cli]":\n\n\tpip install "nexify[cli]"\n'
    raise RuntimeError(message)

from nexify import __version__
from nexify.cli.application import create_app
from nexify.cli.deploy import app as deploy_app
from nexify.cli.init import app as init_app
from rich import print
from rich.console import Console
from rich.logging import RichHandler

app, logger = create_app()


def version_callback(value: bool) -> None:
    if value:
        print(f"Nexify version: [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[  # noqa: ARG001
        bool | None,
        typer.Option(
            "--version",
            help="Show the version and exit.",
            callback=version_callback,
        ),
    ] = None,
    verbose: bool = typer.Option(False, help="Enable verbose output"),
) -> None:
    """
    Nexify CLI - The [bold]nexify[/bold] command line app. 😎

    Manage your [bold]Nexify[/bold] projects, deploy your Nexify apps, and more.
    """

    log_level = logging.DEBUG if verbose else logging.INFO

    setup_logging(level=log_level)


def setup_logging(terminal_width: int | None = None, level: int = logging.INFO) -> None:
    logger = logging.getLogger("nexify_cli")
    console = Console(width=terminal_width) if terminal_width else None
    rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
        show_path=False,
        console=console,
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(rich_handler)

    logger.setLevel(level)
    logger.propagate = False


app.add_typer(init_app)
app.add_typer(deploy_app)


def main() -> None:
    app()
