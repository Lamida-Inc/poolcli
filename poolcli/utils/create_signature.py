from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlparse

import click
from bittensor_wallet import Wallet
from rich.panel import Panel

from poolcli.utils.console import Console

try:
    from importlib.metadata import version

    __version__ = version("poolcli")
except ImportError:
    raise


class WalletType(Enum):
    HOTKEY = "hotkey"
    COLDKEY = "coldkey"


def create_siws_signature(wallet: Wallet, nonce: str, api_url: str, type: WalletType = WalletType.COLDKEY):
    parsed_url = urlparse(api_url)
    domain = parsed_url.netloc
    keypair = wallet.coldkey if type == WalletType.COLDKEY else wallet.hotkey
    statement = "Welcome to Pool Operators! Sign in to do required operations"
    issued_at = datetime.now(timezone.utc).isoformat()[:-3] + "Z"  # noqa: UP017
    message = (
        f"{domain} wants you to sign in with your Substrate account:\n"
        f"{keypair.ss58_address}\n\n"
        f"{statement}\n\n"
        f"URI: {api_url}\n"
        f"Version: {__version__}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at}"
    )
    msg = Panel.fit(f"[bold green]{message}")
    Console.print(msg)
    if click.confirm("Continue with wallet signing?"):
        try:
            signature_bytes = keypair.sign(message.encode("utf-8"))
            signature = "0x" + signature_bytes.hex()
            Console.success("Message signed successfully.")
            return signature, message
        except Exception as sign_error:
            Console.error(f"Failed to sign message: {sign_error}")
            return None, None
    else:
        Console.info("Signing cancelled.")
        return None, None
