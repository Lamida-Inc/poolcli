"""Pool management service module."""

from typing import Any, Optional

import requests
from bittensor_wallet import Wallet
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style

from poolcli.core.config import settings
from poolcli.core.constants import apiRoutes
from poolcli.core.key_manager import KeyManager
from poolcli.exceptions import APIError, PoolError
from poolcli.utils.api_client import APIClient
from poolcli.utils.console import Console
from poolcli.utils.create_signature import WalletType, create_siws_signature

console = Console()


class PoolManager:
    """Service for managing pool operations."""

    def __init__(self, backend_url: str = settings.API_URL) -> None:
        self.backend_url = backend_url
        self.api_client = APIClient(self.backend_url)

    def create_pool(self, token: str, pool_config: dict[str, Any]) -> dict[str, Any]:
        """Create a new pool."""
        try:
            response_json = self.api_client.create_request(
                path=apiRoutes.pool.CREATE_POOL, json_data=pool_config, token=token, method="POST"
            )
            return response_json["data"]
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
            Console.info("Didn't see your key? Please try again after few minutes or contact admin")
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
        Console.info("Signing with hotkey...")
        hotkey_sig, hotkeymsg = create_siws_signature(
            wallet=wallet, nonce=selected_key["apiKey"], api_url=self.backend_url, type=WalletType.HOTKEY
        )
        if not hotkey_sig:
            return
        Console.info("Signing with coldkey...")
        coldkey_sig, coldkeymsg = create_siws_signature(
            wallet=wallet, nonce=selected_key["apiKey"], api_url=self.backend_url, type=WalletType.COLDKEY
        )
        if not coldkey_sig:
            return
        pool_config = {
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
            params: dict[str, Any] = {"page": page, "limit": limit}
            if sort_by:
                params["sortBy"] = sort_by
            if order:
                params["order"] = order
            if status:
                params["status"] = status
            response_json = self.api_client.create_request(
                path=apiRoutes.pool.GET_POOL_LIST, token=token, params=params
            )
            return response_json["data"]

        except requests.RequestException as e:
            raise APIError(f"Pool list request failed: {e}")
        except Exception as e:
            raise PoolError(f"Failed to fetch pools: {e}")

    def get_pool(self, token: str, pool_id: str) -> dict[str, Any]:
        """Get detailed information about a specific pool."""
        try:
            response_json = self.api_client.create_request(path=f"{apiRoutes.pool.GET_POOL}/{pool_id}", token=token)
            return response_json["data"]

        except requests.RequestException as e:
            raise APIError(f"Pool get request failed: {e}")
        except Exception as e:
            raise PoolError(f"Failed to fetch pool: {e}")
