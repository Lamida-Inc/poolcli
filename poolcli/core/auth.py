"""Authentication service module."""

import json
from typing import Optional

from bittensor_wallet import Wallet

from poolcli.core.config import settings
from poolcli.core.constants import apiRoutes
from poolcli.exceptions import AuthenticationError
from poolcli.utils.api_client import APIClient
from poolcli.utils.bittensor_utils import get_wallet_by_name
from poolcli.utils.console import Console
from poolcli.utils.create_signature import create_siws_signature
from poolcli.utils.misc import (
    get_config_file,
    get_stored_session,
    store_token,
)


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, backend_url: str = settings.API_URL) -> None:
        self.backend_url = backend_url
        self.api_client = APIClient(self.backend_url)

    def authenticate_with_wallet(
        self,
        wallet_name: str,
        hotkey: str = "default",
        force: bool = False,
        requires_unlock: bool = True,
    ) -> tuple[Optional[str], Optional[Wallet]]:
        """Handle full authentication flow and return token and wallet object."""

        """Handle full authentication flow and return token and wallet object."""
        stored_session = get_stored_session(wallet_name)
        wallet = get_wallet_by_name(wallet_name, hotkey=hotkey)
        if not wallet:
            Console.error(f"Wallet '{wallet_name}' not found.")
            return None, None

        if not force and stored_session and stored_session.get("token", None):
            Console.info("Using existing valid session.")
            if requires_unlock:
                wallet.unlock_coldkey()
            return stored_session["token"], wallet

        Console.warning("No valid session found. Performing fresh authentication...")
        wallet.unlock_coldkey()
        address = wallet.coldkey.ss58_address
        if not address:
            Console.error("Could not retrieve wallet address.")
            return None, None

        Console.info(f"Using address: {address}")

        try:
            response_json = self.api_client.create_request(
                path=apiRoutes.auth.GET_NONCE, params={"walletaddress": address}
            )
            if "data" not in response_json or "nonce" not in response_json["data"]:
                Console.error(f"Invalid nonce response: {response_json}")
                return None, None
            Console.success("Nonce fetched successfully")
            nonce = response_json["data"]["nonce"]
            signature, message = create_siws_signature(wallet=wallet, nonce=nonce, api_url=self.backend_url)
            if not signature:
                return None, None
            # Step 4: Verify with backend
            verify_payload = {
                "address": address,
                "message": message,
                "signature": signature,
            }
            response_json = self.api_client.create_request(
                path=apiRoutes.auth.VERIFY_SIGNATURE, method="POST", json_data=verify_payload
            )
            if "data" not in response_json or "token" not in response_json["data"]:
                Console.error(f"Authentication failed: {response_json}")
                return None, None

            Console.success("Authentication successful! Token stored.")
            token = response_json["data"]["token"]
            store_token(wallet_name, token, self.backend_url, address)
            return token, wallet

        except Exception as e:
            Console.error(f"Authentication error: {e}")
            return None, None

    def check_auth(self, wallet_name: str) -> bool:
        try:
            stored_session = get_stored_session(wallet_name)
            if stored_session and stored_session["token"]:
                response_json = self.api_client.create_request(
                    path=apiRoutes.auth.CHECK_AUTH, token=stored_session["token"]
                )
                if response_json["message"]:
                    return True
            else:
                return False
        except Exception as _e:
            return False

    def logout_all(self) -> None:
        """Clear all stored authentication tokens."""
        config_file = get_config_file()
        if not config_file.exists():
            raise AuthenticationError("No stored sessions found.")

        try:
            with open(config_file) as f:
                config = json.load(f)

            if not config:
                raise AuthenticationError("No stored sessions found.")

            config.clear()

            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            Console.success("All sessions cleared.")
        except Exception as e:
            raise AuthenticationError(f"Failed to clear sessions: {e}")
