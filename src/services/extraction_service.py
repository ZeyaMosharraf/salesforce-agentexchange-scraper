import json
from typing import Any

from src.clients import SalesforceClient
from src.config import filter_config
from src.models.partner_filter import PartnerFilter
from src.utils.logger import logger


class ExtractionService:

    def __init__(self):
        self.client = SalesforceClient()

    def _generate_filter_combinations(
        self,
    ) -> list[tuple[list[str], list[str], str, str]]:
        """
        Generates individual filter combinations (c_list, s_list, c_label, s_label).
        Loops dynamically through configured countries and practice sizes.
        """
        countries = filter_config.countries
        practice_sizes = filter_config.practice_size

        country_items: list[tuple[list[str], str]] = (
            [([c], c) for c in countries] if countries else [([], "")]
        )
        size_items: list[tuple[list[str], str]] = (
            [([s], s) for s in practice_sizes] if practice_sizes else [([], "")]
        )

        combos = []
        for c_list, c_label in country_items:
            for s_list, s_label in size_items:
                combos.append((c_list, s_list, c_label, s_label))
        return combos

    def extract(self) -> list[dict[str, Any]]:
        logger.info("Starting Salesforce extraction")
        combinations = self._generate_filter_combinations()
        logger.info(f"Total filter combinations to query: {len(combinations)}")

        responses = []

        for combo_idx, (c_list, s_list, c_label, s_label) in enumerate(
            combinations, 1
        ):
            query_desc = []
            if c_label:
                query_desc.append(f"Country: {c_label}")
            if s_label:
                query_desc.append(f"Practice Size: {s_label}")
            desc_str = ", ".join(query_desc) if query_desc else "All Records"

            logger.info(f"[{combo_idx}/{len(combinations)}] Querying {desc_str}")
            print(f"\n[Extraction {combo_idx}/{len(combinations)}] Querying: {desc_str}")

            offset = 0
            while True:
                try:
                    filters = PartnerFilter(
                        countries=c_list,
                        practice_size=s_list,
                        expertises=filter_config.expertises,
                        specializations=filter_config.specializations,
                        states=filter_config.states,
                        rating=filter_config.rating,
                        sorted_by=filter_config.sorted_by,
                        limit_size=filter_config.limit_size,
                        offset=offset,
                    )

                    response = self.client.post(filters.to_payload())

                    return_value = response["returnValue"]
                    if isinstance(return_value, str):
                        return_value = json.loads(return_value)

                    # Check for Salesforce error
                    if not return_value.get("isSuccess", True):
                        error = return_value.get("error", "")

                        if "Maximum SOQL offset allowed" in error:
                            logger.warning(
                                f"Reached Salesforce SOQL OFFSET limit at offset {offset} for {desc_str}."
                            )
                            break

                        logger.error(error)
                        raise RuntimeError(error)

                    partners = return_value["results"]["partners"]

                    if not partners:
                        break

                    # Tag each partner with the active query filter metadata
                    for partner_rec in partners:
                        partner_rec["_query_country"] = c_label
                        partner_rec["_query_practice_size"] = s_label

                    response["returnValue"] = return_value
                    responses.append(response)

                    print(
                        f"\r  -> Offset: {offset} | Fetched: {len(partners)} partners",
                        end="",
                        flush=True,
                    )

                    offset += 1

                except Exception:
                    logger.exception(
                        f"Extraction failed for {desc_str} at offset {offset}"
                    )
                    raise

            print()

        logger.info(f"Extraction completed ({len(responses)} total page responses)")
        return responses