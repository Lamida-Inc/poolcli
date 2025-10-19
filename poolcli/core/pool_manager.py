"""Pool management service module."""

from datetime import datetime
from typing import Any, Optional

import click
import requests
from bittensor_wallet import Wallet
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
from rich.panel import Panel

from poolcli.core.config import settings
from poolcli.core.key_manager import KeyManager
from poolcli.exceptions import APIError, PoolError
from poolcli.utils.auth import get_auth_headers
from poolcli.utils.console import Console
from poolcli.utils.error_handler import handle_error

console = Console()


class PoolManager:
    """Service for managing pool operations."""

    def __init__(self, backend_url: str = settings.API_URL) -> None:
        self.backend_url = backend_url

    def create_pool(self, token: str, pool_config: dict[str, Any]) -> dict[str, Any]:
        """Create a new pool."""
        try:
            with Console.ongoing_status("Creating pool"):
                headers = get_auth_headers(token)
                response = requests.post(
                    f"{self.backend_url}/api/v1/pool/create",
                    json=pool_config,
                    headers=headers,
                    timeout=30,
                )
                data = response.json()
                handle_error(data=data, response=response)
                return data["data"]

        except requests.RequestException as e:
            raise APIError(f"Pool creation request failed: {e}")
        except Exception as e:
            raise PoolError(f"Pool creation failed: {e}")

    def start(self, token: str, wallet: Wallet):
        key_manager = KeyManager(self.backend_url)
        keys_result = key_manager.list_developer_keys(token, page=1, limit=100, status="unused")
        unused_keys = keys_result["keys"]

        if not unused_keys:
            Console.warning("No unused developer keys available.")
            Console.info(f"Create one using: poolcli key create --wallet-name {wallet.name}")
            return

        Console.header("Available Unused Developer Keys")
        result = choice(
            message="Please choose a developer key:",
            options=[(i, key["apiKey"]) for i, key in enumerate(unused_keys)],
            default="salad",
            style=Style.from_dict(
                {
                    "selected-option": "bold green",
                }
            ),
        )
        selected_key = unused_keys[result]

        issued_at = datetime.utcnow().isoformat()[:-3] + "Z"
        domain = (
            self.backend_url.split("://")[1].split("/")[0]
            if "://" in self.backend_url
            else self.backend_url.split("/")[0]
        )
        uri = self.backend_url
        version = "1.0.0"
        statement = "Authorize creation of pool for your miner using this developer key."

        # Hotkey message
        address = wallet.hotkey.ss58_address
        hotkeymsg = (
            f"{domain} wants you to sign in with your Substrate account:\n"
            f"{address}\n\n"
            f"{statement}\n\n"
            f"URI: {uri}\n"
            f"Version: {version}\n"
            f"Nonce: {selected_key['apiKey']}\n"
            f"Issued At: {issued_at}"
        )
        Console.info("Hotkey message to sign:")
        msg = Panel.fit(f"[bold green]{hotkeymsg}")
        Console.print(msg)

        if not click.confirm("Sign with hotkey?"):
            Console.info("Cancelled.")
            return

        try:
            hotkey_sig_bytes = wallet.hotkey.sign(hotkeymsg.encode("utf-8"))
            hotkey_sig = "0x" + hotkey_sig_bytes.hex()
            Console.success("Message signed using hotkey")
        except Exception as e:
            Console.error(f"Hotkey signing failed: {e}")
            return

        # Coldkey message
        address = wallet.coldkey.ss58_address
        coldkeymsg = (
            f"{domain} wants you to sign in with your Substrate account:\n"
            f"{address}\n\n"
            f"{statement}\n\n"
            f"URI: {uri}\n"
            f"Version: {version}\n"
            f"Nonce: {selected_key['apiKey']}\n"
            f"Issued At: {issued_at}"
        )
        Console.info("Coldkey message to sign:")
        msg = Panel.fit(f"[bold green]{coldkeymsg}")
        Console.print(msg)

        if not click.confirm("Sign with coldkey?"):
            Console.info("Cancelled.")
            return

        try:
            coldkey_sig_bytes = wallet.coldkey.sign(coldkeymsg.encode("utf-8"))
            coldkey_sig = "0x" + coldkey_sig_bytes.hex()
            Console.success("Coldkey signed.")
        except Exception as e:
            Console.error(f"Coldkey signing failed: {e}")
            return
        uid = 25
        pool_config = {
            "uid": uid,
            "hotkey": wallet.hotkey.ss58_address,
            "coldkey": wallet.coldkey.ss58_address,
            "hotkeymsg": hotkeymsg,
            "hotkeySignature": hotkey_sig,
            "coldkeymsg": coldkeymsg,
            "coldkeySignature": coldkey_sig,
            "key": selected_key["apiKey"],
        }
        pool_manager = PoolManager(self.backend_url)

        Console.info("Creating pool...")
        created = pool_manager.create_pool(token, pool_config)
        pool = created["pool"]
        Console.success("Pool created successfully!")
        Console.display_pool_info_table(pool, created["developerKey"]["apiKey"], title="Pool Info")

    def list_pools(
        self,
        token: str,
        page: int = 1,
        limit: int = 10,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """List pools for the authenticated user."""
        try:
            headers = get_auth_headers(token)
            params: dict[str, Any] = {"page": page, "limit": limit}
            if sort_by:
                params["sortBy"] = sort_by
            if order:
                params["order"] = order
            if status:
                params["status"] = status

            response = requests.get(
                f"{self.backend_url}/api/v1/pool/get/list",
                headers=headers,
                params=params,
                timeout=10,
            )

            data = response.json()
            handle_error(data=data, response=response)

            return data["data"]

        except requests.RequestException as e:
            raise APIError(f"Pool list request failed: {e}")
        except Exception as e:
            raise PoolError(f"Failed to fetch pools: {e}")

    def get_pool(self, token: str, pool_id: str) -> dict[str, Any]:
        """Get detailed information about a specific pool."""
        try:
            headers = get_auth_headers(token)

            response = requests.get(
                f"{self.backend_url}/api/v1/pool/{pool_id}",
                headers=headers,
                timeout=10,
            )

            data = response.json()
            handle_error(data=data, response=response)
            return data["data"]

        except requests.RequestException as e:
            raise APIError(f"Pool get request failed: {e}")
        except Exception as e:
            raise PoolError(f"Failed to fetch pool: {e}")

    def get_metagraph(self, token: str) -> list[dict[str, Any]]:
        """Get the current metagraph for the subnet."""
        try:
            headers = get_auth_headers(token)
            response = requests.get(
                f"{self.backend_url}/api/v1/pool/get/metagraph",
                headers=headers,
                timeout=10,
            )

            data = response.json()
            handle_error(data=data, response=response)

            return data["data"]

        except requests.RequestException as e:
            raise APIError(f"Metagraph request failed: {e}")
        except Exception as e:
            raise PoolError(f"Failed to fetch metagraph: {e}")

    def update_pool(self, token: str, pool_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update pool configuration."""
        try:
            headers = get_auth_headers(token)

            response = requests.put(
                f"{self.backend_url}/api/v1/pool/{pool_id}",
                json=updates,
                headers=headers,
                timeout=30,
            )

            data = response.json()
            handle_error(data=data, response=response)

            return data["data"]

        except requests.RequestException as e:
            raise APIError(f"Pool update request failed: {e}")
        except Exception as e:
            raise PoolError(f"Pool update failed: {e}")

    def delete_pool(self, token: str, pool_id: str) -> bool:
        """Delete a pool."""
        try:
            headers = get_auth_headers(token)

            response = requests.delete(
                f"{self.backend_url}/api/v1/pool/{pool_id}",
                headers=headers,
                timeout=10,
            )
            return response.status_code == 200

        except requests.RequestException as e:
            raise APIError(f"Pool deletion request failed: {e}")
        except Exception as e:
            raise PoolError(f"Pool deletion failed: {e}")
