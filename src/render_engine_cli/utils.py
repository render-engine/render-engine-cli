import importlib
import re
import shutil
import sys
from dataclasses import dataclass
from os import getenv
from pathlib import Path

import click
import toml
from render_engine import Collection, Site
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from slugify import slugify
from toml import TomlDecodeError

CONFIG_FILE_NAME = "pyproject.toml"


@dataclass
class CliConfig:
    """Handles loading and storing the config from disk"""

    @property
    def module_site(self):
        if not self._config_loaded:
            self.load_config()
            self._config_loaded = True
        return self._module_site

    @property
    def collection(self):
        if not self._config_loaded:
            self.load_config()
            self._config_loaded = True
        return self._collection

    @property
    def editor(self):
        if not self._config_loaded:
            self.load_config()
            self._config_loaded = True
        return self._editor

    # Initialize the arguments and default values
    _module_site: str = None
    _collection: str = None
    default_module_site: str = None
    default_collection: str = None
    _editor: str = None
    _config_loaded: bool = False

    def load_config(self, config_file: str = CONFIG_FILE_NAME):
        """Load the config from the file"""
        stored_config = {}
        try:
            with open(config_file) as stored_config_file:
                try:
                    stored_config = (
                        toml.load(stored_config_file).get("tool", {}).get("render-engine", {}).get("cli", {})
                    )
                except TomlDecodeError as exc:
                    click.echo(
                        f"{click.style(f'Encountered an error while parsing {config_file}', fg='red')}\n{exc}\n",
                        err=True,
                    )
                else:
                    click.echo(f"Config loaded from {config_file}")
        except FileNotFoundError:
            click.echo(f"No config file found at {config_file}")

        self._editor = stored_config.get("editor", getenv("EDITOR"))
        if stored_config:
            # Populate the argument variables and default values from the config
            if (module := stored_config.get("module")) and (site := stored_config.get("site")):
                self._module_site = f"{module}:{site}"
            if default_collection := stored_config.get("collection"):
                self._collection = default_collection


config = CliConfig()


def get_site(import_path: str, site: str, reload: bool = False) -> Site:
    """Split the site module into a module and a class name"""
    sys.path.insert(0, ".")
    imported = importlib.import_module(import_path)
    if reload:
        importlib.reload(imported)
    return getattr(imported, site)


def get_site_content_paths(site: Site) -> list[Path | str | None]:
    """Get the content paths from the route_list in the Site"""

    base_paths = map(lambda x: getattr(x, "content_path", None), site.route_list.values())
    base_paths = list(filter(None, base_paths))
    base_paths.extend(site.static_paths)
    if site.template_path:
        base_paths.append(site.template_path)
    return list(filter(None, base_paths))


def remove_output_folder(output_path: Path) -> None:
    """Remove the output folder"""

    # TODO: #778 Should we check for Operating System
    if output_path.exists():
        shutil.rmtree(output_path)


def split_module_site(module_site: str) -> tuple[str, str]:
    """splits the module_site into a module and a class name"""
    try:
        import_path, site = module_site.split(":", 1)
    except ValueError:
        raise click.exceptions.BadParameter(
            "module_site must be of the form `module:site`",
        )
    return import_path, site


def get_available_themes(console: Console, site: Site, theme_name: str) -> list[str]:
    """Returns the list of available themes to the Console"""
    try:
        return site.theme_manager.prefix[theme_name].list_templates()
    except KeyError:
        console.print(f"[bold red]{theme_name} not installed[bold red]")
        return []


def create_collection_entry(content: str | None, collection: Collection, **context):
    """Creates a new entry for a collection"""
    return collection.Parser.create_entry(content=content, **collection._metadata_attrs(), **context)


def split_args(args: list[str] | None) -> dict[str, str]:
    if not args:
        return {}
    split_arguments = {}
    for arg in args:
        # Accept arguments that are split with either `:` or `=`. Raise a ValueError if neither is found
        split_arg = re.split(r"[:=]", arg, maxsplit=1)
        if len(split_arg) != 2:
            raise ValueError(
                f"Invalid argument: {repr(arg)}. Arguments must have the "
                f"key, value pair separated by either an = or a :"
            )
        k, v = map(str.strip, split_arg)
        if k in split_arguments:
            # Do not allow redefinition of arguments
            raise ValueError(f"Key {repr(k)} is already defined.")
        split_arguments[k] = v
    return split_arguments


def display_filtered_templates(title: str, templates_list: list[str], filter_value: str) -> None:
    """Display filtered templates based on a given filter value."""
    table = Table(title=title)
    table.add_column("[bold blue]Templates[bold blue]")
    for template in templates_list:
        if filter_value in template:
            table.add_row(f"[cyan]{template}[cyan]")
    rprint(table)


def validate_module_site(ctx: dict, param: str, value: str) -> str:
    """Validate the module/site parameter"""
    if value:
        split_module_site(value)
        return value
    else:
        config = CliConfig()
        if config.module_site and split_module_site(config.module_site):
            return config.module_site
    raise click.exceptions.BadParameter("module_site must be in the form of module:site")


def validate_collection(ctx: dict, param: click.Option, value: str) -> str:
    """Validate the collection option"""
    if value:
        return value
    if config.collection:
        return config.collection
    raise click.exceptions.BadParameter("collection must be specified.")


def validate_file_name_or_slug(ctx: click.Context, param: click.Option, value: str) -> str | None:
    """Validate the filename and slug options"""
    if value:
        if " " in value:
            raise click.exceptions.BadParameter(f"Spaces are not allowed in {param.name}.")
        click.echo(f"Setting {param.name} to {value}")
        return value
    if (title_or_slug := ctx.params.get("title")) or (title_or_slug := ctx.params.get("slug")):
        slugged = slugify(title_or_slug)
        value = slugged + ".md" if param.name == "filename" else slugged
        click.echo(f"Setting {param.name} to {value}")
        return value
    if param.name == "filename":
        raise click.exceptions.BadParameter("One of filename, title, or slug must be provided.")
    return None


def get_editor(ctx: click.Context, param: click.Option, value: str) -> str | None:
    """Get the appropriate editor"""
    match value.casefold():
        case "default":
            return config.editor
        case "none":
            return None
        case _:
            return value


def handle_content_file(ctx: click.Context, param: click.Option, value: str) -> str | None:
    """Handle the content file"""
    if value is None:
        return ""
    if value == "stdin":
        content = list()
        click.secho('Please enter the content. To finish, put a "." on a blank line.', fg="green")
        while (line := input("")) != ".":
            content.append(line)
        return "\n".join(content)
    path = Path(value)
    if not path.exists() or path.is_dir():
        raise click.exceptions.BadParameter(
            f'Either the path to a file or "stdin" must be provided. {repr(value)} is invalid.'
        )
    return path.read_text()
