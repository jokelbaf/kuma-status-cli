"""Command line interface of kuma-status-cli."""

import dataclasses
import json
import typing

import rich.console
import typer

import kuma_status_cli.client as client
import kuma_status_cli.config as config
import kuma_status_cli.render as render

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    help="Show the status of every Uptime Kuma status page in the terminal or as JSON.",
)

JsonOption = typing.Annotated[bool, typer.Option("--json", help="Print the snapshot as JSON.")]
BeatsOption = typing.Annotated[int, typer.Option("--beats", min=1, max=100, help="Heartbeats to include per monitor.")]
UrlOption = typing.Annotated[str | None, typer.Option("--url", help="Base URL of the Uptime Kuma instance.")]
LoginOption = typing.Annotated[str | None, typer.Option("--login", help="Uptime Kuma username.")]
PasswordOption = typing.Annotated[str | None, typer.Option("--password", help="Uptime Kuma password.")]
NoVerifyOption = typing.Annotated[bool, typer.Option("--no-verify", help="Save without checking the credentials.")]


def _fail(message: str, as_json: bool) -> typing.NoReturn:
    """Report an error on stderr, or as JSON on stdout, and exit."""
    if as_json:
        typer.echo(json.dumps({"error": message}, indent=2))
    else:
        rich.console.Console(stderr=True).print(f"[bold #FF5370]Error[/]  {message}", soft_wrap=True, highlight=False)
    raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def status(ctx: typer.Context, as_json: JsonOption = False, beats: BeatsOption = 40) -> None:
    """Print the status of every configured status page."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        settings = config.load()
        snapshot = client.fetch(settings, beats=beats)
    except (config.ConfigError, client.ClientError) as error:
        _fail(str(error), as_json)

    if as_json:
        typer.echo(json.dumps(dataclasses.asdict(snapshot), indent=2))
        return

    render.render(rich.console.Console(), snapshot, beats)


@app.command()
def configure(
    url: UrlOption = None,
    login: LoginOption = None,
    password: PasswordOption = None,
    no_verify: NoVerifyOption = False,
) -> None:
    """Store the Uptime Kuma URL and credentials used by this CLI."""
    console = rich.console.Console()
    try:
        existing = config.load()
    except config.ConfigError:
        existing = None

    resolved_url = url or str(typer.prompt("Uptime Kuma URL", default=existing.url if existing else None))
    resolved_login = login or str(typer.prompt("Username", default=existing.username if existing else None))
    resolved_password = password or str(typer.prompt("Password", hide_input=True))

    try:
        settings = config.Config(
            url=config.normalize_url(resolved_url),
            username=resolved_login,
            password=resolved_password,
        )
    except config.ConfigError as error:
        _fail(str(error), False)

    version: str | None = None
    if not no_verify:
        try:
            version = client.check(settings)
        except client.ClientError as error:
            _fail(str(error), False)

    path = config.save(settings)
    suffix = f" (Uptime Kuma v{version})" if version else ""
    console.print(f"[bold #5CDD8B]Saved[/]  {path}{suffix}", soft_wrap=True, highlight=False)


def main() -> None:
    """Entry point of the kuma-status-cli executable."""
    app()
