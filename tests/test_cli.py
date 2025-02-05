from nexify import __version__
from nexify.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == f"Nexify version: {__version__}\n"
