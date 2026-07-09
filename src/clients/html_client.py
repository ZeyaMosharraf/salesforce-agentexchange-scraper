import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import settings
from src.utils.logger import logger


class HtmlClient:

    def __init__(self):

        self.session = self._create_session()

        self.headers = {
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
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(
            max_retries=retry
        )

        session.mount(
            "https://",
            adapter
        )

        session.mount(
            "http://",
            adapter
        )

        return session

    def get(self, url: str) -> str:

        try:

            logger.info(
                f"Downloading HTML: {url}"
            )

            response = self.session.get(
                url=url,
                headers=self.headers,
                timeout=settings.request_timeout,
            )

            logger.info(
                f"Status Code: {response.status_code}"
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as e:

            logger.error(
                f"Failed to download HTML: {e}"
            )

            raise