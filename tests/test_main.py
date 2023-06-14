from typer.testing import CliRunner

from somesy.main import app

runner = CliRunner()


def test_app_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "somesy version: " in result.stdout

    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "somesy version: " in result.stdout
