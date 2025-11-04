"""Refund management service module."""

from datetime import datetime, timedelta
from typing import Any, Optional

import requests
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
from rich.table import Table

from poolcli.core.constants import apiRoutes
from poolcli.core.key_manager import KeyManager
from poolcli.exceptions import APIError, RefundError
from poolcli.utils.api_client import APIClient
from poolcli.utils.console import Console


class RefundManager:
    """Handles refund creation and listing."""

    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.api_client = APIClient(self.backend_url)

    def _is_older_than_one_month(self, updated_at: str) -> bool:
        """Check if a key was last updated more than 1 month ago."""
        try:
            # Parse the ISO format datetime string
            updated_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            one_month_ago = datetime.now(updated_date.tzinfo) - timedelta(days=30)
            return updated_date < one_month_ago
        except (ValueError, TypeError):
            return False

    def create_refund_invoice(self, token: str) -> Optional[dict[str, Any]]:
        """Create refund invoice for developer key."""
        try:
            key_manager = KeyManager(self.backend_url)
            keys_result = key_manager.list_developer_keys(token, page=1, limit=100, status="expired")
            expired_keys = keys_result["keys"]

            if len(expired_keys) == 0:
                return
            else:
                eligible_keys = [key for key in expired_keys if self._is_older_than_one_month(key.get("updatedAt", ""))]

                if len(eligible_keys) == 0:
                    Console.warning("No expired keys older than 1 month found.")
                    return
                else:
                    Console.header("Expired Developer Keys - Available for Refund")
                    result = choice(
                        message="Please choose a developer key:",
                        options=[(i, key["apiKey"]) for i, key in enumerate(eligible_keys)],
                        default="salad",
                        style=Style.from_dict(
                            {
                                "selected-option": "bold green",
                            }
                        ),
                    )
                    selected_key = eligible_keys[result]
                    key_id = selected_key["keyId"]

                    payload = {"keyId": key_id}
                    response = self.api_client.create_request(
                        path=apiRoutes.refund.CREATE_REFUND_INVOICE, method="POST", json_data=payload, token=token
                    )
                    Console.success("✅ Refund Invoice created successfully!")
                    return response["data"]
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        except Exception as e:
            raise RefundError(
                f"Error creating refund invoice: {e}. Check if you have already created invoice for this key."
            )

    def list_refund_invoices(self, token: str, page: int = 1, limit: int = 15) -> dict[str, Any]:
        """List user refund invoices."""
        try:
            params = {"page": page, "limit": limit}
            response = self.api_client.create_request(
                path=apiRoutes.refund.LIST_REFUND_INVOICES, params=params, token=token
            )
            refunds = response["data"].get("data", [])
            pagination = response["data"].get("pagination", {})
            return {"refunds": refunds, "pagination": pagination}
        except requests.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except Exception as e:
            raise RefundError(f"Error listing refunds: {e}")

    def get_refund_details(self, token: str, refund_id: str) -> dict[str, Any]:
        """Fetch detailed refund invoice info."""
        try:
            response = self.api_client.create_request(
                path=f"{apiRoutes.refund.GET_REFUND_DETAILS}/{refund_id}", token=token
            )
            return response.get("data", {})
        except Exception as e:
            raise RefundError(f"Error fetching refund details: {e}")

    def display_refund_list(self, refunds: list[dict[str, Any]], pagination: dict[str, Any]) -> None:
        """Display refunds in a nice table."""
        if not refunds:
            Console.warning("No refund invoices found.")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Refund ID", justify="center")
        table.add_column("Amount", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Created", justify="center")

        for refund in refunds:
            table.add_row(
                refund.get("refundId", "N/A"),
                str(refund.get("amountDue", 5)),
                refund.get("status", "unknown").upper(),
                refund.get("createdAt", "N/A")[:19],
            )

        Console.print(table)
        Console.info(f"Page {pagination.get('page', 1)} of {pagination.get('totalPages', 1)}")
