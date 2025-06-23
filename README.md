## Render Engine CLI

[![PyTest](https://github.com/render-engine/render-engine-cli/actions/workflows/test.yml/badge.svg)](https://github.com/render-engine/render-engine-cli/actions/workflows/test.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Discord](https://img.shields.io/discord/1174377880118104156?label=Discord&color=purple)](https://discord.gg/2xMQ4j4d8m)

Render Engine CLI is the CLI tool for the Render Engine static site generator.

## Learn More

- [CLI Documentation](https://render-engine.readthedocs.io/en/latest/cli/)
- [Check out the Render Engien Documentation](https://render-engine.readthedocs.io/en/latest/)
- [Contributors and Builders, Check out the Wiki](https://github.com/render-engine/render-engine/wiki)
- [Join the community!](https://discord.gg/2xMQ4j4d8m)

## Installing the Render Engine CLI

To use the render engine, you must have Python 3.10 or greater installed. You can download Python from [python.org](https://python.org).

- Linux/MacOS: [python.org](https://python.org)
- Windows: [Microsoft Store](https://apps.microsoft.com/store/detail/python-311/9NRWMJP3717K)

The Render Engine CLI is available in PyPI and can be installed via `pip` or `uv`:

```shell
pip install render-engine-cli     # via pip
uv pip install render-engine-cli  # via uv
```

Since render engine itself is one of the dependencies of the CLI there is no need to isntall
them separately. With that, the version of render engine in the CLI dependencies is not pinned
to a specific version so if you want to pin it you can do so either in your `requirements.txt`
(`pip`) or `pyproject.toml` (`uv`) files.

```shell
# requirements.text
render-engine-cli
render-engine==<version to pin>


# pyproject.toml
[project]
dependencies = [
  "render-engine-cli",
  "render-engine==<version to pin>"
]
```

## Getting Started

Check out the [Getting Started](https://render-engine.readthedocs.io/en/latest/page/) Section in the [Documentation](https://render-engine.readthedocs.io)
