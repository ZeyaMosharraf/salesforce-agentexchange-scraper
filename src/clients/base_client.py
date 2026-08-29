import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.utils.logger import logger


class BaseClient:
    """Base HTTP client with exponential backoff and retry handling."""

    def _create_session(self, allowed_methods: list[str] | None = None) -> requests.Session:
        logger.debug("Creating HTTP session with retry adapter")
        session = requests.Session()

        methods = allowed_methods or ["GET", "POST"]
        retry = Retry(
            total=3,
            backoff_factor=2.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(methods),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session
