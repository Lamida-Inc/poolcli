"""Custom exceptions for poolcli."""


class PoolcliError(Exception):
    """Base exception for poolcli."""
    pass


class AuthenticationError(PoolcliError):
    """Raised when authentication fails."""
    pass


class WalletError(PoolcliError):
    """Raised when wallet operations fail."""
    pass


class KeyManagementError(PoolcliError):
    """Raised when key management operations fail."""
    pass


class PoolError(PoolcliError):
    """Raised when pool operations fail."""
    pass


class APIError(PoolcliError):
    """Raised when API requests fail."""
    pass
