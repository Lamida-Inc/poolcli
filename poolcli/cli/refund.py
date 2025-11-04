"""Refund management CLI commands."""

import time

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
def start(wallet_name: str, backend_url: str) -> None:
    """Create refund invoice for a developer key."""
    Console.header("💸 Creating refund invoice for developer key")

    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name, requires_unlock=False)

        if not token:
            Console.error("Authentication required.")
            return

        refund_manager = RefundManager(backend_url)
        refund_response = refund_manager.create_refund_invoice(token)
        refund_invoice = refund_response.get("invoice", {})
        amount = refund_invoice.get("amountDue", 5)

        if refund_response:
            Console.success("✅ Refund invoice created successfully!")
            Console.print_table(
                "Refund Invoice Details",
                [
                    f"ID: {refund_response.get('refundId', 'N/A')}",
                    f"Amount: {amount} TAO",
                    f"Status: {refund_response.get('status', 'unknown').upper()}",
                ],
            )
        else:
            Console.warning("No refund invoice returned. See if your developer key is expired or not.")

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
        refund_details = refund_manager.get_refund_details(token, refund_id)
        invoice = refund_details.get("invoice", {})

        Console.print_table(
            f"Refund {refund_id}",
            [
                f"{'Status:':<20} {refund_details.get('status', 'unknown').upper()}",
                f"{'Amount:':<20} {invoice.get('amountDue', 0)} TAO",
                f"{'Created:':<20} {invoice.get('createdAt', 'N/A')}",
                f"{'Updated:':<20} {invoice.get('updatedAt', 'N/A')}",
            ],
        )

    except (AuthenticationError, RefundError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")
