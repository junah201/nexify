import logging

import typer


def create_app() -> tuple[typer.Typer, logging.Logger]:
    app = typer.Typer()

    logger = logging.getLogger("nexify_cli")

    return app, logger
