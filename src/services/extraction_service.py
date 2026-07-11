from src.clients import SalesforceClient
from src.utils.logger import logger
from src.models.partner_filter import PartnerFilter
from typing import Any
import json

class ExtractionService:

    def __init__(self):

        self.client = SalesforceClient()

    def extract(self) -> list[dict[str, Any]]:

        logger.info("Starting Salesforce extraction")

        responses = []

        offset = 0

        while True:

            try:

                filters = PartnerFilter(
                    offset=offset
                )

                response = self.client.post(
                    filters.to_payload()
                )

                # Stop if Salesforce returns no partners

                return_value = response["returnValue"]

                if isinstance(return_value, str):
                    return_value = json.loads(return_value)

                partners = return_value["results"]["partners"]

                if not partners:

                    logger.info(
                        "No more partners found. Extraction completed."
                    )

                    break

                responses.append(response)

                logger.info(
                    f"Fetched offset {offset} ({len(partners)} partners)"
                )

                print(
                f"\r[Extraction] Offset: {offset} | Partners: {len(partners)}",
                end="",
                flush=True,
                )

                offset += 1

            except Exception:

                logger.exception(
                    f"Extraction failed at offset {offset}"
                )

                raise
            
            print()

        logger.info(
            f"Extraction completed ({len(responses)} responses)"
        )

        return responses