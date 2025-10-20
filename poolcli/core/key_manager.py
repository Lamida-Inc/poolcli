"""Key management service module."""

from typing import Any, Optional

import requests
from rich.table import Table

from poolcli.core.config import settings
from poolcli.core.constants import apiRoutes
from poolcli.exceptions import APIError, KeyManagementError
from poolcli.utils.api_client import APIClient
from poolcli.utils.console import Console


class KeyManager:
    """Service for managing developer keys."""

    def __init__(self, backend_url: str = settings.API_URL) -> None:
        self.backend_url = backend_url
        self.api_client = APIClient(self.backend_url)

    def create_invoice(self, token: str) -> Optional[dict[str, Any]]:
        """Create invoice + developer key (inactive until paid)."""
        try:
            payload = {"amountDue": 5.0, "currency": "TAO", "purpose": "buy_key"}
            response_json = self.api_client.create_request(
                path=apiRoutes.key.CREATE_INVOICE, json_data=payload, token=token, method="POST"
            )

            invoice_data = response_json["data"]
            Console.success("✅ Invoice created successfully!")
            table = Table(show_header=True)
            table.add_column("Invoice Details", justify="center")
            table.add_row(f"Id: {invoice_data['invoiceId']}")
            Console.print(table)
            return invoice_data
        except requests.RequestException as e:
            raise APIError(f"Failed to create invoice: {e}")
        except Exception as e:
            raise KeyManagementError(f"Failed to create invoice: {e}")

    def display_invoice_status(self, token: str, invoice_id: str) -> tuple[bool, Optional[str]]:
        """Display invoice status and return (is_paid, developer_key)."""
        invoice = self._get_invoice_details(token, invoice_id)
        status: str = invoice.get("status", "unknown")
        is_paid = status == "paid"
        status_icon = "✅" if is_paid else "⏳"
        developer_key = invoice.get("apiKey")
        Console.print_table(
            f"{status_icon} Invoice {invoice_id}",
            [
                f"{'Status:':<20} {status.upper()}",
                f"{'Amount:':<20} {invoice.get('amountDue', 0)} TAO",
                f"{'TX Hash:':<20} {invoice.get('txHash', 'N/A')[:20] + '...' if invoice.get('txHash') else 'N/A'}",
                f"{'Paid At:':<20} {invoice.get('paidAt', 'Not Paid')[:19] + '...' if invoice.get('paidAt') else 'N/A'}",  # noqa: E501
            ],
        )

        return is_paid, developer_key

    def _get_invoice_details(self, token: str, invoice_id: str) -> dict[str, Any]:
        """Get detailed invoice information."""
        try:
            response_json = self.api_client.create_request(
                path=f"{apiRoutes.key.GET_INVOICE}/{invoice_id}", token=token
            )
            return response_json.get("data", {})  # type: ignore
        except Exception:
            return {}

    def list_developer_keys(
        self, token: str, page: int = 1, limit: int = 15, status: Optional[str] = None
    ) -> dict[str, Any]:
        """list all developer keys for a wallet."""
        try:
            params = {"page": page, "limit": limit, "sortBy": "createdAt", "order": "desc"}
            if status:
                params["status"] = status
            response_json = self.api_client.create_request(path=apiRoutes.key.GET_DEV_KEYS, params=params, token=token)
            if response_json.get("data") is None:
                raise KeyManagementError("Invalid response: 'data' field is None")

            keys_data = response_json["data"].get("data", [])
            pagination = response_json["data"].get("pagination", {})

            Console.display_keys_table(keys_data)
            return {"keys": keys_data, "pagination": pagination}
        except requests.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except Exception as e:
            raise KeyManagementError(f"Error fetching keys: {e}")

    def display_keys_list(self, keys_data: list[dict[str, Any]], pagination: dict[str, Any], wallet_name: str) -> None:
        """Display developer keys in a 3-column table."""
        if not keys_data:
            Console.warning("No developer keys found for this wallet.")
            Console.info(f"Create a new key: poolcli key create --wallet-name {wallet_name}")
            return

        Console.success(f"Found {pagination.get('total', len(keys_data))} developer key(s)\n")

        rows = []
        for idx, key in enumerate(keys_data, 1):
            key_display = key.get("apiKey", "N/A")
            key_status = key.get("status", "unknown").upper()
            rows.append([str(idx), key_display, key_status])

        # Pagination info
        if pagination:
            total_pages = pagination.get("totalPages", 1)
            current_page = pagination.get("page", 1)
            Console.info(f"Page {current_page} of {total_pages}")
            if current_page < total_pages:
                Console.info(f"Next page: poolcli key list --wallet-name {wallet_name} --page {current_page + 1}")
