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

            if e.response.status_code == 404:

                logger.warning(
                    f"HTML page not found: {url}"
                )

                return None

            raise

        except requests.RequestException as e:

            logger.error(
                f"Failed to download HTML: {e}"
            )

            raise