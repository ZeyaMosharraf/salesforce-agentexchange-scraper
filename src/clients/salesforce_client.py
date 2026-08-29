from typing import Any
import requests

from src.clients.base_client import BaseClient
from src.config import settings
from src.utils.logger import logger


class SalesforceClient(BaseClient):
    """Client for querying the Salesforce AppExchange Apex API."""

    def __init__(self):
        self.session = self._create_session(allowed_methods=["POST"])
        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://appexchange.salesforce.com",
            "Referer": "https://appexchange.salesforce.com/",
            "User-Agent": settings.user_agent,
        }

    def post(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.session.post(
                url=settings.api_url,
                json=payload,
                headers=self.headers,
                timeout=settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception(f"Salesforce API request failed: {e}")
            raise