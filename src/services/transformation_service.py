from concurrent.futures import ThreadPoolExecutor
from typing import Any

from src.clients.html_client import HtmlClient
from src.config import settings
from src.transformations.deduplicate_transformation import (
    DeduplicateTransformation,
)
from src.transformations.html_transformation import HtmlTransformation
from src.transformations.merge_transformation import MergeTransformation
from src.transformations.partner_transformation import PartnerTransformation
from src.utils.logger import logger


class TransformationService:
    """
    Coordinates concurrent HTML downloading, parsing, deduplication, and data enrichment
    for extracted partner listings.
    """

    def __init__(self):
        self.html_client = HtmlClient()
        self.partner_transformation = PartnerTransformation()
        self.deduplicate_transformation = DeduplicateTransformation()
        self.html_transformation = HtmlTransformation()
        self.merge_transformation = MergeTransformation()

    def transform(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        logger.info("Starting transformation pipeline")

        try:
            # 1. Parse raw API responses into partner dictionaries
            raw_partners = self.partner_transformation.transform(raw_data)

            # 2. Deduplicate partners before performing network enrichment
            unique_partners = self.deduplicate_transformation.transform(raw_partners)

            # 3. Concurrently enrich each unique partner with web details
            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                transformed_partners = list(
                    executor.map(self.process_partner, unique_partners)
                )

            logger.info(
                f"Transformation completed for {len(transformed_partners)} partners"
            )
            return transformed_partners

        except Exception:
            logger.exception("Transformation pipeline failed")
            raise

    def process_partner(self, partner: dict[str, Any]) -> dict[str, Any]:
        url = partner.get("listing_url")
        if not url:
            partner["html_status"] = "No URL"
            return partner

        try:
            html = self.html_client.get(url)

            if html is None:
                partner["html_status"] = "Not Found"
                return partner

            html_data = self.html_transformation.transform(html)
            partner["html_status"] = "Success"
            return self.merge_transformation.transform(partner, html_data)

        except Exception as e:
            logger.warning(
                f"Failed to enrich partner '{partner.get('name', 'Unknown')}' ({url}): {e}"
            )
            partner["html_status"] = "Enrichment Error"
            return partner