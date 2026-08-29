import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.logger import logger


class BaseClient:
    """Base HTTP client with exponential backoff and retry handling."""

    def _create_session(self, allowed_methods: list[str] | None = None) -> requests.Session:
        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=allowed_methods or ["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session
