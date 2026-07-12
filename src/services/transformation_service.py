from typing import Any
from src.utils.logger import logger

from src.clients.html_client import HtmlClient
from src.transformations.html_transformation import HtmlTransformation
from src.transformations.partner_transformation import PartnerTransformation
from src.transformations.merge_transformation import MergeTransformation

from concurrent.futures import ThreadPoolExecutor
from src.config import settings


class TransformationService:

    def __init__(self):

        self.html_client = HtmlClient()

        self.partner_transformation = PartnerTransformation()

        self.html_transformation = HtmlTransformation()

        self.merge_transformation = MergeTransformation()

    def transform(self, raw_data: list[dict[str, Any]],) -> list[dict[str, Any]]:

        logger.info("Starting transformation pipeline")

        transformed_partners = []

        try:

            partners = self.partner_transformation.transform(raw_data)

            logger.info(f"Received {len(partners)} partners from API transformation")

            with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:

                transformed_partners = list(
                    executor.map(
                        self.process_partner,
                        partners
                    )
                )

            logger.info(
                f"Transformation completed for {len(transformed_partners)} partners"
            )

            return transformed_partners

        except Exception:

            logger.exception(
                "Transformation pipeline failed"
            )

            raise

    def process_partner(self,partner: dict[str, Any]) -> dict[str, Any]:

        html = self.html_client.get(
            partner["listing_url"]
        )

        if html is None:

            partner["html_status"] = "Not Found"

            return partner

        html_data = self.html_transformation.transform(
            html
        )

        return self.merge_transformation.transform(
            partner,
            html_data,
        )