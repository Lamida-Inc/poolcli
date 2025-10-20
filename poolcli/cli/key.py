"""Key management CLI commands."""

import time
import traceback
from typing import Optional

import click

from poolcli.core.auth import AuthService
from poolcli.core.config import settings
from poolcli.core.key_manager import KeyManager
from poolcli.core.pool_manager import PoolManager
from poolcli.exceptions import APIError, AuthenticationError, KeyManagementError
from poolcli.utils.console import Console

console = Console()


@click.group(name="key")
def key() -> None:
    """Create/list developer keys."""
    pass


@key.command()
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name.")
@click.option(
    "--hotkey",
    prompt="Wallet hotkey, if not provided (default) will be used",
    default="default",
    help="Wallet hotkey to create developer key (use single hotkey for single dk.)",
)
@click.option("--backend-url", default=settings.API_URL)
@click.option("--force", is_flag=True, help="Force re-authentication")
def create(
    wallet_name: str,
    hotkey: str,
    backend_url: str,
    force: bool,
) -> None:
    """Authenticate and create developer key invoice."""
    Console.header(f"🔐 Authenticating with '{wallet_name}'")
    try:
        # Authenticate
        auth_service = AuthService(backend_url)
        token, wallet = auth_service.authenticate_with_wallet(wallet_name, hotkey, force)

        if not token:
            Console.error("Authentication failed.")
            return

        Console.print_table(
            "✅ Authentication Complete",
            [
                f"{'Wallet:':<20} {wallet_name}",
                f"{'Token:':<20} {token[:20]}...{token[-10:]}",
            ],
        )

        key_manager = KeyManager(backend_url)
        result = key_manager.create_invoice(token)

        if not result:
            Console.error("Failed to create invoice + key.")
            return
        invoice_id = result["invoiceId"]
        amount = result["amountDue"]
        dest = result["receiverAddress"]
        if click.confirm(f"🚀 Proceed with {amount} TAO payment to get developer key?"):
            success = False
            import bittensor as bt

            with console.payment_status(amount, dest):
                # subtensor = bt.subtensor(network="test")  # uncomment this for test
                subtensor = bt.subtensor()
                success = subtensor.transfer(wallet=wallet, dest=dest, amount=bt.Balance.from_tao(amount=amount))
                time.sleep(5)  # give time for listener to synchronize transactions
            if success:
                Console.print(f"[bold green] Successfully transferred {amount} TAO to {dest}\n")
                if click.confirm("Proceed with creating pool?"):
                    pool_manager = PoolManager(backend_url=backend_url)
                    pool_manager.start(token=token, wallet=wallet)
            else:
                Console.info(f"Invoice {invoice_id} created. ")
        else:
            Console.info(f"Invoice {invoice_id} created. ")

    except (AuthenticationError, KeyManagementError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@key.command()
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=15, help="Keys per page")
@click.option(
    "--status",
    type=click.Choice(["active", "expired", "unused"]),
    help="Filter by status",
)
def list(wallet_name: str, backend_url: str, page: int, limit: int, status: Optional[str]) -> None:
    """list all developer keys for a wallet."""
    Console.header(f"🔑 Fetching developer keys for '{wallet_name}'")

    try:
        # Get valid token
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name=wallet_name, requires_unlock=False)
        if not token:
            Console.error("Authentication failed.")
            return

        # Fetch keys
        key_manager = KeyManager(backend_url)
        result = key_manager.list_developer_keys(token, page, limit, status)
        key_manager.display_keys_list(result["keys"], result["pagination"], wallet_name)

    except (AuthenticationError, KeyManagementError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@key.group()
def invoice() -> None:
    """Invoice management commands."""
    pass


@invoice.command()
@click.option("--invoice-id", required=True, prompt="Invoice Id", help="Invoice Id to fetch")
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
def get(invoice_id: str, wallet_name: str, backend_url: str) -> None:
    """Get invoice status."""
    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name=wallet_name, requires_unlock=False)

        if not token:
            Console.error("Authentication required. Run: poolcli auth login")
            return

        key_manager = KeyManager(backend_url)
        is_paid, _ = key_manager.display_invoice_status(token, invoice_id)

        if is_paid:
            Console.success("Invoice has been paid!")
        else:
            Console.warning("Invoice is still pending payment.")

    except (AuthenticationError, KeyManagementError, APIError) as e:
        print(traceback.format_exc())
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    key()
