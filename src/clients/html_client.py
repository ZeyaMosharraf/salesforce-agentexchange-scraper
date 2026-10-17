import threading
import requests

from src.clients.base_client import BaseClient
from src.config import settings
from src.utils.logger import logger


class HtmlClient(BaseClient):
    """Client for downloading HTML listing pages from AppExchange with thread-safe sessions."""

    def __init__(self):
        self._local = threading.local()
        self.headers = {
            "User-Agent": settings.user_agent,
        }

    @property
    def session(self) -> requests.Session:
        """Returns a thread-local requests.Session instance."""
        if not hasattr(self._local, "session"):
            self._local.session = self._create_session(allowed_methods=["GET"])
        return self._local.session

    def get(self, url: str) -> str | None:
        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=settings.request_timeout,
            )
            response.raise_for_status()
            return response.text

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"HTML page not found: {url}")
                return None
            raise

        except requests.RequestException as e:
            logger.error(f"Failed to download HTML from '{url}': {e}")
            raise