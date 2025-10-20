"""Pool management CLI commands."""

import click

from poolcli.core.auth import AuthService
from poolcli.core.config import settings
from poolcli.core.pool_manager import PoolManager
from poolcli.exceptions import APIError, AuthenticationError, PoolError
from poolcli.utils.console import Console


@click.group(name="pool")
def pool() -> None:
    """Manage pools."""
    pass


@pool.command()
@click.option("--wallet-name", required=True, prompt="Wallet name")
@click.option(
    "--hotkey",
    prompt="Wallet hotkey (default if not provided)",
    default="default",
)
@click.option("--backend-url", default=settings.API_URL)
@click.option("--force", is_flag=True, help="Force re-authentication")
def create(
    wallet_name: str,
    hotkey: str,
    backend_url: str,
    force: bool,
) -> None:
    """Create a new pool."""
    Console.header(f"🏊 Creating new pool for wallet '{wallet_name}'")
    try:
        auth_service = AuthService(backend_url)
        token, wallet = auth_service.authenticate_with_wallet(wallet_name, hotkey, force)

        if not token or not wallet:
            Console.error("Authentication failed.")
            return

        pool_manager = PoolManager(backend_url=backend_url)
        pool_manager.start(token=token, wallet=wallet)

    except (AuthenticationError, PoolError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@pool.command()
@click.option("--wallet-name", required=True, prompt="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=15, help="Pools per page")
@click.option("--force", is_flag=True, help="Force re-authentication")
def list(wallet_name: str, backend_url: str, page: int, limit: int, force: bool) -> None:
    """List all pools for authenticated user (tabular view)."""
    Console.header(f"🏊 Listing pools for '{wallet_name}'")

    try:
        auth_service = AuthService(backend_url)
        token, wallet = auth_service.authenticate_with_wallet(wallet_name=wallet_name, requires_unlock=False)

        if not token:
            Console.error("Authentication required. Run: poolcli auth login")
            return

        pool_manager = PoolManager(backend_url)
        result = pool_manager.list_pools(token, page, limit)

        pools = result.get("data", [])
        pagination = result.get("pagination", {})

        Console.display_pools_list_multi_column(pools, pagination)

    except (AuthenticationError, PoolError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


@pool.command()
@click.option("--pool-id", required=True, prompt="Pool Id")
@click.option("--wallet-name", required=True, prompt="Wallet name")
@click.option("--backend-url", default=settings.API_URL)
def show(pool_id: str, wallet_name: str, backend_url: str) -> None:
    """Show detailed information about a specific pool."""
    Console.header(f"🔍 Pool Details: {pool_id}")

    try:
        auth_service = AuthService(backend_url)
        token, _ = auth_service.authenticate_with_wallet(wallet_name)

        if not token:
            Console.error("Authentication required. Run: poolcli auth login")
            return

        pool_manager = PoolManager(backend_url)
        pool_data = pool_manager.get_pool(token, pool_id)

        Console.print_table(
            f"Pool: {pool_data.get('poolId', pool_id)}",
            [
                f"{'ID:':<20} {pool_data.get('poolId', 'N/A')}",
                f"{'UID:':<20} {pool_data.get('uid', 'N/A')}",
                f"{'Status:':<20} {pool_data.get('status', 'unknown').upper()}",
                f"{'Hotkey:':<20} {pool_data.get('hotkey', 'N/A')[:20]}...",
                f"{'Coldkey:':<20} {pool_data.get('coldkey', 'N/A')[:20]}...",
                f"{'Created:':<20} {pool_data.get('createdAt', 'N/A')[:19] if pool_data.get('createdAt') else 'N/A'}",
                f"{'Updated:':<20} {pool_data.get('updatedAt', 'N/A')[:19] if pool_data.get('updatedAt') else 'N/A'}",
            ],
        )

    except (AuthenticationError, PoolError, APIError) as e:
        Console.error(str(e))
    except Exception as e:
        Console.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    pool()
