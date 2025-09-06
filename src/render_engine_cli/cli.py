import datetime
import json
import re
import subprocess
from pathlib import Path

import click
from dateutil import parser as dateparser
from dateutil.parser import ParserError
from render_engine import Collection
from rich.console import Console

from render_engine_cli.event import ServerEventHandler
from render_engine_cli.utils import (
    create_collection_entry,
    display_filtered_templates,
    get_available_themes,
    get_editor,
    get_site,
    get_site_content_paths,
    handle_content_file,
    remove_output_folder,
    split_args,
    split_module_site,
    validate_collection,
    validate_file_name_or_slug,
    validate_module_site,
)


@click.group()
def app():
    print("App invoked.")
    ...


@app.command
@click.option(
    "-e",
    "--extra-context",
    help="Extra context to pass to the cookiecutter template. This must be a JSON string",
    default=None,
    type=click.STRING,
)
@click.option(
    "-t",
    "--template",
    help="Template tcd ..o use for creating a new site.",
    default="https://github.com/render-engine/cookiecutter-render-engine-site",
    type=click.STRING,
)
@click.option(
    "--no-input",
    is_flag=True,
    default=False,
    help="Do not prompt for parameters.",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(
        path_type=Path,
        exists=False,
    ),
    default=Path("./"),
)
@click.option(
    "-c",
    "--config-file",
    type=click.Path(
        path_type=Path,
        exists=True,
        readable=True,
    ),
    default=None,
)
def init(template: str, extra_context: str, no_input: bool, output_dir: Path, config_file: Path):
    """
    Create a new site configuration. You can provide extra_context to the cookiecutter template.

    Also, any argument that cookiecutter accepts can be passed to this command.

    The template can be a local path or a git repository.
    """

    # Check if cookiecutter is installed
    try:
        from cookiecutter.main import cookiecutter
    except ImportError:
        click.secho(
            "You need to install cookiecutter to use this command. Run `pip install cookiecutter` to install it.",
            err=True,
            fg="red",
        )
        raise click.Exit(0)
    extra_context = json.loads(extra_context) if extra_context else None
    cookiecutter(
        template=template,
        extra_context=extra_context,
        output_dir=output_dir,
        config_file=config_file,
        no_input=no_input,
    )


@app.command
@click.option(
    "--module-site",
    type=click.STRING,
    # help="The module (python file) and site (the Site object) for your site in the format module:site",
    callback=validate_module_site,
)
@click.option(
    "-c",
    "--clean",
    help="Clean the output folder prior to building.",
    is_flag=True,
    default=False,
)
def build(module_site: str, clean: bool):
    print("Running the build...")
    module, site_name = split_module_site(module_site)
    site = get_site(module, site_name)
    if clean:
        remove_output_folder(Path(site.output_path))
    site.render()


@app.command
@click.option(
    "--module-site",
    type=click.STRING,
    # help="The module (python file) and site (the Site object) for your site in the format module:site",
    callback=validate_module_site,
)
@click.option(
    "-c",
    "--clean",
    help="Clean the output folder prior to building.",
    is_flag=True,
    default=False,
)
@click.option(
    "-r",
    "--reload",
    help="Reload on changes to the site.",
    is_flag=True,
    default=False,
)
@click.option("-p", "--port", type=click.IntRange(0, 65534), help="Port to serve on", default=8000.0)
def serve(module_site: str, clean: bool, reload: bool, port: int):
    """
    Create an HTTP server to serve the site at `localhost`.

    !!! warning
        this is only for development purposes and should not be used in production.

    Params:
        module_site: Python module and initialize Site class
        reload: Use to reload server on file change
        build: flag to build the site prior to serving the app
        directory: Directory to serve. If `module_site` is provided, this will be the `output_path` of the site.
        port: Port to serve on
    """
    if not module_site:
        raise click.exceptions.BadParameter("You need to specify module:site")
    module, site_name = split_module_site(module_site)
    site = get_site(module, site_name)

    if clean:
        remove_output_folder(Path(site.output_path))
    site.render()

    server_address = ("127.0.0.1", port)

    handler = ServerEventHandler(
        import_path=module,
        server_address=server_address,
        dirs_to_watch=get_site_content_paths(site) if reload else None,
        site=site_name,
        output_path=site.output_path,
        patterns=None,
        ignore_patterns=[r".*output\\*.+$", r"\.\\\..+$", r".*__.*$"],
    )

    with handler:
        pass


@app.command
@click.option(
    "--module-site",
    type=click.STRING,
    # help="The module (python file) and site (the Site object) for your site in the format module:site",
    callback=validate_module_site,
)
@click.option(
    "--collection",
    type=click.STRING,
    help="The name of the collection to add the entry to.",
    callback=validate_collection,
)
@click.option(
    "--content",
    default=None,
    help="The content to include in the page. Either this or --content-file may be specified but not both.",
    type=click.STRING,
)
@click.option(
    "--content-file",
    type=click.STRING,
    callback=handle_content_file,
    default=None,
    help="Path to a file containing the desired content. Using 'stdin' will ask you to enter the content in "
    "the terminal. Either this or `--content` may be provided but not both",
)
@click.option(
    "-t",
    "--title",
    type=click.STRING,
    help="Title for the new entry.",
    default=None,
)
@click.option(
    "-s",
    "--slug",
    type=click.STRING,
    help="Slug for the new page.",
    callback=validate_file_name_or_slug,
)
@click.option(
    "-d",
    "--include-date",
    is_flag=True,
    default=False,
    help="Include today's date in the metadata for your entry.",
)
@click.option(
    "-a",
    "--args",
    multiple=True,
    type=click.STRING,
    help="key value attrs to include in your entry use the format `--args key=value` or `--args key:value`",
)
@click.option(
    "-e",
    "--editor",
    default="default",
    type=click.STRING,
    callback=get_editor,
    help="Select the editor to use. If not set the default editor (as set by the EDITOR environment variable) "
    "will be used. If 'none' is set no editor will be launched.",
)
@click.option(
    "-f",
    "--filename",
    type=click.STRING,
    help="The filename in which to save the path. Will be saved in the collection's `content_path` [REQUIRED]",
    callback=validate_file_name_or_slug,
)
def new_entry(
    module_site: str,
    collection: str,
    content: str,
    content_file: str,
    title: str,
    slug: str,
    include_date: bool,
    args: list[str],
    editor: str,
    filename: str,
):
    """Creates a new collection entry based on the parser. Entries are added to the Collections content_path"""
    parsed_args = split_args(args) if args else {}
    # There is an issue with including `title` in the context to the parser that causes an exception. We can fix
    # this by popping it out of the arguments here and using regex to push it back in later.
    _title = parsed_args.pop("title", None)
    # Prefer the title keyword from the one provided in `--args` in case someone does both.
    title = title or _title
    if slug:
        # If `slug` is provided as a keyword add it to the `parsed_args` to be included in the rendering.
        # Prefer the keyword to what is passed via `--args`
        parsed_args["slug"] = slug
    # Verify that we have a valid date should it be supplied or requested
    if date := parsed_args.pop("date", None):
        try:
            date = dateparser.parse(date)
        except ParserError:
            raise ValueError(f"Invalid date: {repr(date)}.") from None
    elif include_date:
        date = datetime.datetime.today()
    if date:
        parsed_args["date"] = date

    module, site_name = split_module_site(module_site)
    site = get_site(module, site_name)
    _collection: Collection
    if not (
        _collection := next(
            coll for coll in site.route_list.values() if type(coll).__name__.lower() == collection.lower()
        )
    ):
        raise click.exceptions.BadParameter(f"Unknown collection: {collection}")
    filepath = Path(_collection.content_path).joinpath(filename)
    if filepath.exists():
        if not click.confirm(
            f"File {filename} exists are {_collection.content_path} - do you wish to overwrite that file?"
        ):
            click.secho("Aborting new entry.", fg="yellow")
            return
    if content and content_file:
        raise TypeError("Both content and content_file provided. At most one may be provided.")
    if content_file:
        content = content_file
    entry = create_collection_entry(content=content or "", collection=_collection, **parsed_args)
    if title:
        # If we had a title earlier this is where we replace the default that is added by the template handler with
        # the one supplied by the user.
        entry = re.sub(r"title: Untitled Entry", f"title: {title}", entry)
    filepath.write_text(entry)
    Console().print(f'New {collection} entry created at "{filepath}"')

    if editor:
        subprocess.run([editor, filepath])


@app.command
@click.option(
    "--module-site",
    type=click.STRING,
    # help="The module (python file) and site (the Site object) for your site in the format module:site",
    callback=validate_module_site,
)
@click.option(
    "-t",
    "--theme-name",
    type=click.STRING,
    help="Theme to search templates in.",
    default="",
)
@click.option(
    "-f",
    "--filter-value",
    type=click.STRING,
    help="Filter templates based on names.",
    default="",
)
def templates(module_site: str, theme_name: str, filter_value: str):
    """
    CLI for listing available theme templates.

    Params:
        module_site: Python module and initialize Site class
        theme_name: Optional. Specifies the theme to list templates from.
        filter_value: Optional. Filters templates based on provided names.
    """
    module, site_name = split_module_site(module_site)
    site = get_site(module, site_name)
    console = Console()

    if theme_name:
        available_themes = get_available_themes(console, site, theme_name)
        if available_themes:
            display_filtered_templates(
                f"[bold green]Available templates for {theme_name} [bold green]",
                available_themes,
                filter_value,
            )
    else:
        console.print("[red]No theme name specified. Listing all installed themes and their templates[red]")
        for theme_prefix, theme_loader in site.theme_manager.prefix.items():
            templates_list = theme_loader.list_templates()
            display_filtered_templates(
                f"[bold green]Showing templates for {theme_prefix}[bold green]",
                templates_list,
                filter_value,
            )


if __name__ == "__main__":
    app()
