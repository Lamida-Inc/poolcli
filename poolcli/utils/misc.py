import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from poolcli.core.config import settings


def get_config_file() -> Path:
    """Get the config file path."""
    config_path = settings.CONFIG_PATH
    config_path.mkdir(exist_ok=True)
    return config_path / "config.json"


def store_token(wallet_name: str, token: str, backend_url: str, address: str) -> None:
    """Store authentication token and metadata."""
    config_file = get_config_file()
    config = {}

    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
        except Exception as _e:
            config = {}

    config[wallet_name] = {
        "token": token,
        "backend_url": backend_url,
        "address": address,
        "created_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
        "last_used": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def get_stored_session(wallet_name: str) -> Optional[dict[str, dict[str, str]]]:
    """Retrieve stored session for a wallet."""
    config_file = get_config_file()
    if not config_file.exists():
        return None

    try:
        with open(config_file) as f:
            config = json.load(f)
        session: dict = config.get(wallet_name, {})
        created_at = datetime.fromisoformat(session.get("created_at", None))
        if not created_at:
            return None
        if datetime.now(timezone.utc) - created_at > timedelta(minutes=50):  # Consider re-auth after 24h  # noqa: UP017
            return None

        return session
    except Exception as _e:
        return None


def clear_session(wallet_name: str) -> None:
    """Clear stored session for a wallet."""
    config_file = get_config_file()
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            if wallet_name in config:
                del config[wallet_name]
                with open(config_file, "w") as f:
                    json.dump(config, f, indent=2)
        except Exception as _e:
            pass


def get_auth_headers(token: Optional[str]) -> dict[str, str]:
    """Get headers with Bearer token for API calls."""
    if token:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    else:
        return {"Content-Type": "application/json"}
