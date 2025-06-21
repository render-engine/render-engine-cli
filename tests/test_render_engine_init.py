import json

import pytest
from click.testing import CliRunner

from render_engine_cli.cli import app


@pytest.fixture(scope="module", autouse=True)
def get_test_template(tmp_path_factory):
    path = tmp_path_factory.getbasetemp()
    project_slug = path.joinpath("{{cookiecutter.project_slug}}")
    project_slug.mkdir()
    project_slug.joinpath("app.py").write_text("hello {{cookiecutter.world}}")
    path.joinpath("cookiecutter.json").write_text(json.dumps({"world": "world", "project_slug": "testslug"}))

    return path.resolve()


@pytest.fixture
def runner():
    """CLI test runner fixture"""
    yield CliRunner()


def tests_error_raised_if_cookiecutter_not_installed(request, mocker, runner, get_test_template):
    """Tests that an error is raised if cookiecutter is not installed"""

    # Mock importing cookiecutter
    mocker.patch("cookiecutter.main.cookiecutter", side_effect=ImportError)

    result = runner.invoke(
        app,
        [
            "init",
            "--extra-context",
            json.dumps(
                {
                    "project_slug": request.node.name,
                }
            ),
            "--template",
            get_test_template,
            "--no-input",
        ],
    )
    assert isinstance(result.exception, ImportError)


def test_init_local_path_extra_context(request, tmp_path, get_test_template, runner):
    """
    Tests that you can call init using a local path

    It also tests that the extra_context is passed to the template.
    """
    runner.invoke(
        app,
        [
            "init",
            "--extra-context",
            json.dumps(
                {
                    "project_slug": request.node.name,
                }
            ),
            "--template",
            get_test_template,
            "--no-input",
            "--output-dir",
            tmp_path,
        ],
    )

    template_path = tmp_path.joinpath(request.node.originalname)
    app_py = template_path.joinpath("app.py")
    assert app_py.exists()
    assert app_py.read_bytes() == b"hello world"


def test_init_called_with_config(request, tmp_path, tmp_path_factory, runner):
    """
    Tests that you can call init with cookiecutter configs passed in through a config file.
    """
    temp_file = tmp_path.joinpath("test_cookiecutter_args.json")
    temp_file.write_text(
        f"""
default_context:
    world: "Earth"
    project_slug: {request.node.originalname}
"""
    )
    runner.invoke(
        app,
        [
            "init",
            "--extra-context",
            json.dumps(
                {
                    "project_slug": request.node.name,
                }
            ),
            "--template",
            str(tmp_path_factory.getbasetemp().resolve()),
            "--no-input",
            "--output-dir",
            tmp_path,
            "--config-file",
            temp_file,
        ],
    )
    output_path = tmp_path.joinpath(request.node.originalname)
    app_py = output_path.joinpath("app.py")
    assert app_py.exists()
    assert app_py.read_bytes() == b"hello Earth"
