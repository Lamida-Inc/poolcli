"""Wallet management CLI commands."""

import click

from poolcli.core.wallet_manager import WalletManager
from poolcli.utils.console import Console


@click.group(name="wallet")
def wallet() -> None:
    """Inspect Bittensor wallets."""
    pass


@wallet.command(name="list")
def list_wallets() -> None:
    """
    list all available coldkey wallets and their associated hotkeys with addresses.

    This command scans the wallet directory and displays all found coldkeys
    and their hotkeys with SS58 addresses (read from public keys, no password needed).
    """
    try:
        wallet_manager = WalletManager()
        wallets = wallet_manager.get_all_wallets()
        wallet_manager.display_wallets_tree(wallets)
    except Exception as e:
        Console.error(f"Failed to list wallets: {e}")


if __name__ == "__main__":
    wallet()
