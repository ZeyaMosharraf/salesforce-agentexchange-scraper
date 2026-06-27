import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import settings


class SalesforceClient:

    def __init__(self):

        self.session = self._create_session()

        self.headers = {
            "Content-Type": "application/json",
            "Origin": "https://appexchange.salesforce.com",
            "Referer": "https://appexchange.salesforce.com/",
            "User-Agent": settings.user_agent,
        }

    def _create_session(self) -> requests.Session:

        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=["POST"],
        )

        adapter = HTTPAdapter(max_retries=retry)

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def post(self, payload: dict) -> dict:

        response = self.session.post(
            url=settings.api_url,
            json=payload,
            headers=self.headers,
            timeout=settings.request_timeout,
        )

        response.raise_for_status()

        return response.json()