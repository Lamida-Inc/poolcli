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

    def create_refund_invoice(self, token: str) -> Optional[dict[str, Any]]:
        """Create refund invoice for developer key."""
        try:
            key_manager = KeyManager(self.backend_url)
            keys_result = key_manager.list_developer_keys(token=token, page=1, limit=100, status="expired")
            expired_keys = keys_result["keys"]

            if not expired_keys:
                return
            else:
                Console.header("Expired Developer Keys - Available for Refund")
                result = choice(
                    message="Please choose a developer key:",
                    options=[(i, key["apiKey"]) for i, key in enumerate(expired_keys)],
                    default="salad",
                    style=Style.from_dict(
                        {
                            "selected-option": "bold green",
                        }
                    ),
                )
                selected_key = expired_keys[result]
                key_id = selected_key["keyId"]

                payload = {"keyId": key_id}
                response = self.api_client.create_request(
                    path=apiRoutes.refund.CREATE_REFUND_INVOICE, method="POST", json_data=payload, token=token
                )
                data = response.get("data", {})
                Console.print_table(
                    "Refund Invoice Details",
                    [
                        f"{'ID':<25} {data.get('refundId', 'N/A')}",
                        f"{'Amount':<25} {data.get('amount')} TAO",
                        f"{'Status':<25 } {data.get('status', 'unknown').upper()}",
                        f"{'Created:':<25} {self.to_full_date(data.get('createdAt'))}",
                        f"{'Estimated refund Date:':<25} {self._get_estimated_refund_date(data.get('createdAt')).strftime('%A, %B %d, %Y')}",  # noqa: E501
                    ],
                )
                Console.success("✅ Refund Invoice created successfully!")
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        except Exception as e:
            raise RefundError(f"Error creating refund invoice: {e}.")

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
            refund_details = response.get("data", {})
            invoice = refund_details.get("invoice", {})

            Console.print_table(
                f"Refund {refund_id}",
                [
                    f"{'Status:':<25} {refund_details.get('status', 'unknown').upper()}",
                    f"{'Amount:':<25} {invoice.get('amountDue', 0)} TAO",
                    f"{'Created:':<25} {self.to_full_date(invoice.get('createdAt'))}",
                    f"{'Estimated refund Date:':<25} {self._get_estimated_refund_date(invoice.get('createdAt')).strftime('%A, %B %d, %Y')}",  # noqa: E501
                ],
            )

        except Exception as e:
            raise RefundError(f"Error fetching refund details: {e}")

    def to_full_date(self, date: str):
        return datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")

    def _get_estimated_refund_date(self, date: str):
        updated_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        one_month_after = datetime.now(updated_date.tzinfo) + timedelta(days=30)
        return one_month_after

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
        table.add_column("Estimated Refund Date")

        for refund in refunds:
            table.add_row(
                refund.get("refundId", "N/A"),
                str(refund.get("amountDue", 5)),
                refund.get("status", "unknown").upper(),
                str(self.to_full_date(refund.get("createdAt"))),
                str(self._get_estimated_refund_date(refund.get("createdAt"))),
            )

        Console.print(table)
        Console.info(f"Page {pagination.get('page', 1)} of {pagination.get('totalPages', 1)}")
