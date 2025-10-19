"""Wallet management service module."""



from poolcli.utils.bittensor_utils import WalletInfo, get_wallets
from poolcli.utils.console import Console


class WalletManager:
    """Service for managing wallet operations."""

    def __init__(self) -> None:
        pass

    def get_all_wallets(self) -> list[WalletInfo]:
        """Get all available wallets."""
        Console.header("🔎 Searching for Wallets")
        wallets = get_wallets()

        if not wallets:
            Console.warning("No wallets found.")
            Console.info("You can create a new wallet using the Bittensor CLI: `btcli wallet create`")

        return wallets

    def display_wallets_tree(self, wallets: list[WalletInfo]) -> None:
        Console.print_tree(wallets)

