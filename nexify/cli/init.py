import importlib.resources
import shutil
from pathlib import Path

import typer
from nexify.cli.application import create_app
from rich import print

app, logger = create_app()


@app.command()
def init() -> None:
    """
    Initialize a Nexify project.
    """
    app_name = typer.prompt("Enter the project name")
    service_name = app_name.replace(" ", "").lower()

    dest = Path.cwd() / app_name
    src = str(importlib.resources.files("nexify").joinpath("templates/basic"))

    if dest.exists():
        print(f"Directory {dest} already exists.")
        raise typer.Exit(1)

    shutil.copytree(src, dest)

    # Update nexify.yml
    setting_path = dest / "nexify.json"
    with open(setting_path, encoding="utf-8") as f:
        content = f.read()

    content = content.replace("${nexify:SERVICE_NAME}", service_name)

    with open(setting_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f":tada: Project [blue]{app_name}[/blue] created at [bright_green]'{dest}'[/bright_green]")
