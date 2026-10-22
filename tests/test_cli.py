from typer.testing import CliRunner
from comic2svg.cli import app
from comic2svg import __version__

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_presets():
    result = runner.invoke(app, ["presets"])
    assert result.exit_code == 0
    assert "vintage-comic" in result.stdout
    assert "clean-line" in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "comic2svg" in result.stdout
    assert "convert" in result.stdout
