"""CLI command modules for poolcli."""

from poolcli.cli.auth import auth
from poolcli.cli.key import key
from poolcli.cli.pool import pool
from poolcli.cli.wallet import wallet

__all__ = [
    "auth",
    "key",
    "pool",
    "wallet",
]
