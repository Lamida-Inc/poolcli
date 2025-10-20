from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from poolcli.core.constants import Constants


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_URL: str = Constants.TAOMININGPOOL_API_URL
    CONFIG_PATH: Path = Path.home() / ".poolcli"


settings = Settings()
