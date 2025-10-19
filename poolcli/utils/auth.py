import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests


def get_config_path() -> Path:
    """Get the poolcli config directory path."""
    return Path.home() / ".poolcli"


def get_config_file() -> Path:
    """Get the config file path."""
    config_path = get_config_path()
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
        "created_at": datetime.utcnow().isoformat(),
        "last_used": datetime.utcnow().isoformat(),
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def get_stored_session(wallet_name: str) -> Optional[dict[str, Any]]:
    """Retrieve stored session for a wallet."""
    config_file = get_config_file()
    if not config_file.exists():
        return None

    try:
        with open(config_file) as f:
            config = json.load(f)
        session: dict = config.get(wallet_name, {})

        # Check if token is still valid (rough check - JWT expiry should be verified by backend)
        created_at = datetime.fromisoformat(session.get("created_at", datetime.utcnow().isoformat()))
        if datetime.utcnow() - created_at > timedelta(hours=24):  # Consider re-auth after 24h
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


def get_auth_headers(token: str) -> dict[str, str]:
    """Get headers with Bearer token for API calls."""
    return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}


def is_authenticated(backend_url: str, token: str) -> bool:
    """Verify if token is still valid by making a test request."""
    try:
        headers = get_auth_headers(token)
        response = requests.get(f"{backend_url}/pool/get/metagraph/sync-time", headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as _e:
        return False
