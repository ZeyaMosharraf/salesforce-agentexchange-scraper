"""
Transformation Service.

Coordinates data transformation, deduplication, and concurrent HTML enrichment
for extracted AppExchange partner listings with live terminal progress statistics.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from src.clients.html_client import HtmlClient
from src.config import settings
from src.transformations.appexchange_transformation import (
    AppExchangeTransformation,
)
from src.transformations.deduplicate_transformation import (
    DeduplicateTransformation,
)
from src.transformations.html_transformation import HtmlTransformation
from src.transformations.merge_transformation import MergeTransformation
from src.utils.logger import logger


class TransformationService:
    """
    Coordinates HTML downloading, parsing, deduplication, and data enrichment
    for extracted partner listings.
    """

    def __init__(self):
        self.html_client = HtmlClient()
        self.appexchange_transformation = AppExchangeTransformation()
        self.deduplicate_transformation = DeduplicateTransformation()
        self.html_transformation = HtmlTransformation()
        self.merge_transformation = MergeTransformation()

    def transform(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        logger.info("Starting transformation pipeline")

        try:
            # 1. Parse raw AppExchange API responses into standardized partner dictionaries
            raw_partners = self.appexchange_transformation.transform(raw_data)
            print(f"\n[Transformation] Normalized {len(raw_partners)} partner records from API responses")

            # 2. Deduplicate partners before performing network enrichment
            unique_partners = self.deduplicate_transformation.transform(raw_partners)

            # 3. Concurrently enrich each unique partner with web details (with live progress tracking)
            total_partners = len(unique_partners)
            print(
                f"\n[HTML Enrichment] Starting concurrent detail scraping for {total_partners} partners "
                f"(Worker Threads: {settings.max_workers})"
            )

            results: list[dict[str, Any]] = [{} for _ in range(total_partners)]
            completed = 0
            success_count = 0
            not_found_count = 0
            error_count = 0

            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                future_to_index = {
                    executor.submit(self.process_partner, partner): idx
                    for idx, partner in enumerate(unique_partners)
                }

                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    result = future.result()
                    results[idx] = result
                    completed += 1

                    status = result.get("html_status", "Success")
                    if status == "Success":
                        success_count += 1
                    elif status == "Not Found":
                        not_found_count += 1
                    else:
                        error_count += 1

                    pct = (completed / total_partners) * 100 if total_partners > 0 else 100.0
                    print(
                        f"\r  -> Enriched: {completed}/{total_partners} ({pct:.1f}%) | "
                        f"Success: {success_count} | 404: {not_found_count} | Errors: {error_count}",
                        end="",
                        flush=True,
                    )

            print("\n  -> HTML Enrichment completed successfully.")
            logger.info(
                f"Transformation completed for {len(results)} partners "
                f"(Success: {success_count}, 404: {not_found_count}, Errors: {error_count})"
            )
            return results

        except Exception:
            logger.exception("Transformation pipeline failed")
            raise

    def process_partner(self, partner: dict[str, Any]) -> dict[str, Any]:
        partner_copy = partner.copy()
        url = partner_copy.get("listing_url")

        if not url:
            partner_copy["html_status"] = "No URL"
            return self.merge_transformation.transform(partner_copy, {})

        try:
            html = self.html_client.get(url)

            if html is None:
                partner_copy["html_status"] = "Not Found"
                return self.merge_transformation.transform(partner_copy, {})

            html_data = self.html_transformation.transform(html)
            partner_copy["html_status"] = "Success"
            return self.merge_transformation.transform(partner_copy, html_data)

        except Exception as e:
            logger.warning(
                f"Failed to enrich partner '{partner_copy.get('name', 'Unknown')}' ({url}): {e}"
            )
            partner_copy["html_status"] = "Enrichment Error"
            return self.merge_transformation.transform(partner_copy, {})