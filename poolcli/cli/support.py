import click
from rich.table import Table

from poolcli.utils.console import Console


@click.group(name="support")
def support() -> None:
    """Manage pools."""
    pass


@support.command()
def info():
    table = Table(show_lines=False, show_header=False, title="[magenta]Support")
    table.add_column()
    table.add_column()
    informations = {
        "[cyan]email": "[green]admin@bettertherapy.ai",
        "[cyan]discord": "[green]https://discord.gg/uxze2nyT4G",
    }
    for [key, value] in informations.items():
        table.add_row(key, value)
    Console.print(table)
