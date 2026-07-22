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

                # Check for Salesforce error first
                if not return_value.get("isSuccess", True):
                    error = return_value.get("error", "")

                    if "Maximum SOQL offset allowed" in error:
                        logger.warning(
                            "Reached Salesforce SOQL OFFSET limit (2000 rows). "
                            f"Last attempted offset: {offset}. "
                            "Stopping extraction gracefully."
                        )
                        break

                    logger.error(error)
                    raise RuntimeError(error)

                partners = return_value["results"]["partners"]

                if not partners:

                    logger.info(
                        "No more partners found. Extraction completed."
                    )

                    break

                responses.append(response)

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