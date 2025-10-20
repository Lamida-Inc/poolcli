import importlib.metadata

import click

# Import the new command groups
from poolcli.cli.auth import auth
from poolcli.cli.key import key
from poolcli.cli.pool import pool
from poolcli.cli.support import support
from poolcli.cli.wallet import wallet
from poolcli.utils.help import RecursiveHelpGroup


@click.group(invoke_without_command=True)
@click.option("-v", "--version", "show_version", is_flag=True, help="Show version and exit")
@click.option("--commands", is_flag=True, help="Show available commands and exit")
@click.pass_context
def cli(ctx, show_version: bool, commands: bool) -> None:
    """
    🌊 poolcli: A CLI for managing Bittensor subnet pool operations.
    """
    if show_version:
        click.echo(f"poolcli {importlib.metadata.version('poolcli')}")
        ctx.exit(0)
    elif commands:
        # Temporarily use RecursiveHelpGroup for recursive help
        original_cls = cli.__class__
        try:
            cli.__class__ = RecursiveHelpGroup
            click.echo(cli.get_help(ctx))
        finally:
            cli.__class__ = original_cls
        ctx.exit(0)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


# Register the command groups with the main CLI
cli.add_command(auth)
cli.add_command(wallet)
cli.add_command(key)
cli.add_command(pool)
cli.add_command(support)

if __name__ == "__main__":
    try:
        cli(standalone_mode=False)
    except click.Abort:
        click.echo("\nOperation aborted by user.", err=True)
    except click.ClickException as e:
        e.show()
    except Exception as e:
        click.echo(click.style(f"\nUnexpected error: {e}", fg="red", bold=True))
