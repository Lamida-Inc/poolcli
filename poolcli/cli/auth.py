"""Authentication CLI commands."""

import click

from poolcli.core.auth import AuthService
from poolcli.core.config import settings
from poolcli.exceptions import APIError, AuthenticationError
from poolcli.utils.console import Console


@click.group(name="auth")
def auth() -> None:
    """Authentication commands."""
    pass


@auth.command()
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name.")
@click.option(
    "--hotkey",
    prompt="Wallet hotkey, if not provided (default) will be used",
    default="default",
    help="Hotkey name associated with the wallet, 'default' hotkey will be used if not provided.",
)
@click.option("--backend-url", default=settings.API_URL)
@click.option("--force", is_flag=True, help="Force re-authentication even if valid session exists")
def login(
    wallet_name: str,
    hotkey: str,
    backend_url: str,
    force: bool,
) -> None:
    """Authenticate with wallet."""
    Console.header(f"🔐 Authenticating with '{wallet_name}'")

    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name, hotkey, force)

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

    except (AuthenticationError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@auth.command()
def logout() -> None:
    """Clear stored authentication tokens."""
    try:
        auth_service = AuthService()
        auth_service.logout_all()
    except AuthenticationError as e:
        Console.warning(str(e))
    except Exception as e:
        Console.error(f"Failed to logout: {e}")


@auth.command()
@click.option("--wallet-name", required=True, prompt="Wallet name", help="Wallet name.")
@click.option("--backend-url", default=settings.API_URL)
def status(wallet_name: str, backend_url: str) -> None:
    """Check authentication status for a wallet."""
    try:
        auth_service = AuthService(backend_url)
        status = auth_service.check_auth(wallet_name)

        if status:
            Console.success(f"✅ Authenticated as {wallet_name}")
        else:
            Console.warning(f"❌ Not authenticated as {wallet_name}")
            Console.info("Run 'poolcli auth login' to authenticate.")
    except Exception as e:
        Console.error(f"Error checking status: {e}")


if __name__ == "__main__":
    auth()
