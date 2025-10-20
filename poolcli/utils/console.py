"""Console output utilities"""

import time
from typing import Any, Optional

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class Colors:
    """ANSI color codes"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"


# Singleton Rich console
console = RichConsole()
tree = Tree("Wallets", style="bold bright_blue")


class Console:
    """Console output helper using Rich"""

    @staticmethod
    def success(msg: str) -> None:
        """Print success message"""
        console.print(f"✓ [green]{msg}[/green]")

    @staticmethod
    def error(msg: str) -> None:
        """Print error message"""
        console.print(f"✗ [red]{msg}[/red]")

    @staticmethod
    def warning(msg: str) -> None:
        """Print warning message"""
        console.print(f"⚠ [yellow]{msg}[/yellow]")

    @staticmethod
    def info(msg: str) -> None:
        """Print info message"""
        console.print(f"ℹ [cyan]{msg}[/cyan]")

    @staticmethod
    def header(msg: str) -> None:
        """Print header message"""
        console.print(Panel(Text(msg, style="bold magenta"), expand=False))

    @staticmethod
    def payment_status(amount, dest):
        """Print payment status"""
        return console.status(f"[bold green]Transferring {amount} TAO to {dest}\n", spinner="earth")

    @staticmethod
    def ongoing_status(msg):
        return console.status(f"[bold green]{msg}", spinner="earth")

    @staticmethod
    def print(msg: str, style: Optional[str] = None, bold: bool = False) -> None:
        """Print arbitrary message with optional style"""
        if bold:
            msg = f"[bold]{msg}[/bold]"
        if style:
            msg = f"[{style}]{msg}[/{style}]"
        console.print(msg)

    @staticmethod
    def loading_spinner(message: str, duration: float = 2.0) -> None:
        """Show a loading spinner"""
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[cyan]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description=message, total=None)
            time.sleep(duration)
            progress.remove_task(task)

    @staticmethod
    def print_table(title: str, rows: list[str]) -> None:
        """Print a single-column table"""
        table = Table(title=title, show_lines=True, expand=False)
        table.add_column("Items", style="bold")
        for row in rows:
            table.add_row(row)
        console.print(table)

    @staticmethod
    def print_tree(wallets):
        for w in wallets:
            # Add the coldkey as a branch in the tree with address
            coldkey_display = f"Coldkey: [cyan]{w.name}[/cyan]"
            if w.coldkey_address:
                coldkey_display += f" [magenta]{w.coldkey_address}[/magenta]"

            coldkey_branch = tree.add(f"{coldkey_display}\n")
            # Add hotkeys under the coldkey branch with addresses
            if w.hotkeys:
                for hkey in w.hotkeys:
                    hotkey_display = f"Hotkey: [dim][yellow]{hkey['name']}[/yellow][/dim]"
                    if hkey["ss58_address"]:
                        hotkey_display += f" [green]{hkey['ss58_address']}[/green]"

                    coldkey_branch.add(f"{hotkey_display}\n")
            else:
                coldkey_branch.add("[dim]No hotkeys found[/dim]")

        console.print(tree)

    @staticmethod
    def display_keys_table(keys_data: list[dict]) -> None:
        """Display developer keys in a table format."""

        if not keys_data:
            Console.warning("No developer keys found.")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Developer Key", style="cyan")
        table.add_column("Invoice ID", style="green")
        table.add_column("Status", style="yellow")

        for key in keys_data:
            invoice = key.get("invoice")
            invoice_id = invoice.get("invoiceId") if invoice else "N/A"
            status = key.get("status", "unknown").upper()
            table.add_row(key.get("apiKey", "N/A"), invoice_id, status)

        console.print(table)

    @staticmethod
    def display_pool_info_table(pool: dict[str, Any], developerKey: str, title: str = None) -> None:
        """Display pool information in a table format."""

        table = Table(show_header=True, header_style="bold magenta", title=title)
        table.add_column(justify="left")
        table.add_column(justify="right")
        table.add_row("UID", str(pool.get("uid", "N/A")))
        table.add_row("Hot Key", pool.get("hotkey", "N/A"))
        table.add_row("Cold Key", pool.get("coldkey", "N/A"))
        table.add_row("Developer Key", developerKey)
        table.add_row("Status", pool.get("status", "N/A"))

        console.print(table)

    @staticmethod
    def display_pools_list_multi_column(pools: list[dict[str, Any]], pagination: dict[str, Any]) -> None:
        """Display list of pools using table format."""
        from rich.table import Table

        if not pools:
            Console.warning("No pools found.")
            Console.info("Create a new pool: poolcli pool create")
            return

        Console.success(f"Found {pagination.get('total', 0)} pool(s)")

        table = Table(show_header=True, header_style="bold magenta", title="Your Pools")
        table.add_column("#", style="cyan")
        table.add_column("Pool ID", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="blue")

        for idx, pool_data in enumerate(pools, 1):
            pool_id = pool_data.get("poolId", "N/A")
            status = pool_data.get("status", "unknown").upper()
            created_at = pool_data.get("createdAt", "N/A")[:19] if pool_data.get("createdAt") else "N/A"
            table.add_row(str(idx), pool_id, status, created_at)

        console.print(table)

        # Print pagination info
        if pagination:
            total_pages = pagination.get("totalPages", 1)
            current_page = pagination.get("page", 1)
            Console.info(f"Page {current_page} of {total_pages}")
