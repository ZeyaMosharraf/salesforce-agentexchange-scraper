"""
Application configuration.

Loads infrastructure settings from environment variables and exposes
them through a single immutable Settings object.
"""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


def _get_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None or not val.strip():
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    """Application infrastructure and connection settings."""

    api_url: str = os.getenv(
        "API_URL",
        "https://findpartners.salesforce.com/webruntime/api/apex/execute?language=en-US&asGuest=true&htmlEncode=false",
    )
    request_timeout: int = _get_int("REQUEST_TIMEOUT", 30)
    user_agent: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    max_workers: int = _get_int("MAX_WORKERS", 8)


settings = Settings()