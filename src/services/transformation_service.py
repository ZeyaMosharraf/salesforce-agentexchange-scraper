from typing import Any
from src.utils.logger import logger

from src.clients.html_client import HtmlClient
from src.transformations.html_transformation import HtmlTransformation
from src.transformations.partner_transformation import PartnerTransformation
from src.transformations.merge_transformation import MergeTransformation


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

            partners = self.partner_transformation.transform(
                raw_data
            )

            logger.info(
            f"Received {len(partners)} partners from API transformation"
            )

            for partner in partners:
                
                logger.info(
                f"Processing {len(partners)} partners"
                )

                html = self.html_client.get(
                    partner["listing_url"]
                )

                html = self.html_client.get(
                partner["listing_url"]
                )

                if html is None:

                    partner["html_status"] = "Not Found"

                    transformed_partners.append(partner)

                    continue

                html_data = self.html_transformation.transform(html)

                merged_partner = self.merge_transformation.transform(
                    partner,
                    html_data,
                )

                transformed_partners.append(
                    merged_partner
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