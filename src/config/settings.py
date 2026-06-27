"""
Application configuration.

Loads infrastructure settings from environment variables and exposes
them through a single immutable Settings object.
"""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


@dataclass(frozen=True, slots=True)
class Settings:
    """Application infrastructure settings."""

    api_url: str = os.getenv("API_URL", "")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    user_agent: str = os.getenv("USER_AGENT", "Mozilla/5.0")


settings = Settings()