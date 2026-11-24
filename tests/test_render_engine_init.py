import json

import pytest
from click.testing import CliRunner

from render_engine_cli.cli import app


@pytest.fixture
def runner():
    """CLI test runner fixture"""
    yield CliRunner()


def test_init_is_listed_in_the_help(runner):
    """`render-engine --help` lists the init command."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Create a new Render Engine site." in result.output


def test_init_passes_the_arguments_to_render_engine(runner, mocker):
    """All arguments after `init` are passed to render-engine's init, with the CLI's command name."""
    main = mocker.patch("render_engine.init.__main__.main")

    runner.invoke(app, ["init", "--no-input", "-o", "sites", "-e", '{"site_title": "My Blog"}'])

    main.assert_called_once_with(
        ["--no-input", "-o", "sites", "-e", '{"site_title": "My Blog"}'], prog="render-engine init"
    )


def test_init_help_shows_the_init_options(runner):
    """`render-engine init --help` shows the options of render-engine's init, under the CLI's command name."""
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    assert "usage: render-engine init" in result.output
    assert "--no-input" in result.output


def test_init_creates_a_site(runner, tmp_path):
    """`render-engine init --no-input` creates a site from the answers in --extra-context."""
    result = runner.invoke(
        app, ["init", "--no-input", "-o", str(tmp_path), "-e", json.dumps({"site_title": "My Blog"})]
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "my-blog" / "app.py").is_file()


def test_init_template_option_is_rejected(runner):
    """Custom templates are no longer supported, so --template is an error."""
    result = runner.invoke(app, ["init", "--template", "https://github.com/me/my-template"])

    assert result.exit_code == 2
    assert "unrecognized arguments: --template" in result.output
