# Contributing to the Render Engine Projects

Render Engine CLI is the CLI tool for the Render Engin static site generator. Please refer to
the main [CONTRIBUTING.md](https://github.com/render-engine/render-engine/blob/main/CONTRIBUTING.md)
for more details on how to contribute.

## Render Engine CLI Specific Topics

Render Engine CLI is a `uv` based project. For more information on installing `uv` and using it
please see the [uv documentation](https://docs.astral.sh/uv/#installation).To get started, for
this repository and check out your fork.

```shell
git clone <url to fork>
```

Once you have checked out the repository, run `uv sync` and then activate the `venv` that was
created:

```shell
uv sync
source .venv/bin/activate
```

Once you have done this you will be in the virtual environment and ready to work. It is recommended
that you do a local, editable install of the CLI in your virtual environment so that you can easily
work with the changes you have made.

```shell
uv pip install -e .
```

This will allow you to test your changes via the command line.
