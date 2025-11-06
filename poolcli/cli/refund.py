"""Refund management CLI commands."""

import click

from poolcli.core.auth import AuthService
from poolcli.core.config import settings
from poolcli.core.refund_manager import RefundManager
from poolcli.exceptions import APIError, AuthenticationError, RefundError
from poolcli.utils.console import Console

console = Console()


@click.group(name="refund")
def refund() -> None:
    """Manage refunds (create/list/get)."""
    pass


@refund.command()
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
def create(wallet_name: str, backend_url: str) -> None:
    """Create refund invoice for a developer key."""
    Console.header("💸 Creating refund invoice for developer key")

    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name, requires_unlock=False)

        if not token:
            Console.error("Authentication required.")
            return

        refund_manager = RefundManager(backend_url=backend_url)
        refund_manager.create_refund_invoice(token)
    except (AuthenticationError, APIError, RefundError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@refund.command()
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=15, help="Refunds per page")
def list(wallet_name: str, backend_url: str, page: int, limit: int) -> None:
    """List all refund invoices for this wallet."""
    Console.header(f"📜 Listing refunds for wallet '{wallet_name}'")

    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name, requires_unlock=False)
        if not token:
            Console.error("Authentication required.")
            return

        refund_manager = RefundManager(backend_url)
        result = refund_manager.list_refund_invoices(token, page, limit)
        refund_manager.display_refund_list(result["refunds"], result["pagination"])

    except (AuthenticationError, RefundError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@refund.command()
@click.option("--refund-id", required=True, prompt="Refund ID", help="Refund ID")
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
def get(refund_id: str, wallet_name: str, backend_url: str) -> None:
    """Fetch detailed refund invoice info."""
    Console.header(f"🔍 Fetching refund details: {refund_id}")

    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name, requires_unlock=False)

        if not token:
            Console.error("Authentication required.")
            return

        refund_manager = RefundManager(backend_url)
        refund_manager.get_refund_details(token, refund_id)
    except (AuthenticationError, RefundError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")
