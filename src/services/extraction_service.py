"""
Extraction Service.

Coordinates extraction of AppExchange partner listings across configured countries
using the modern AppExchange recommendations REST API and cursor pagination.
"""

from typing import Any

from src.clients.appexchange_client import AppExchangeClient
from src.config import filter_config
from src.config.filters import COUNTRY_TO_LOCATION_CODE
from src.utils.logger import logger


class ExtractionService:
    """Extracts partner listings from AppExchange for all configured countries."""

    def __init__(self):
        self.client = AppExchangeClient()

    def extract(self) -> list[dict[str, Any]]:
        """
        Extracts all listings across configured target countries.
        - If countries is empty ([]): Extracts ALL global listings without geographic restriction.
        - If countries has items: Loops sequentially through each specified country.

        Returns:
            List of raw page response dictionaries.
        """
        countries = filter_config.countries
        listing_type = filter_config.listing_type or "consultants"
        page_size = filter_config.page_size or 100

        # Explicit handling: empty list means ALL records globally (no silent defaulting)
        if not countries:
            logger.info(
                "No country filter specified; extracting ALL listings globally without geographic restriction."
            )
            print(f"\n[Extraction] Location: Global (All Countries) | Type: {listing_type}")

            responses = self.client.fetch_all_pages(
                location=None,
                listing_type=listing_type,
                page_size=page_size,
            )

            for resp in responses:
                resp["_query_country"] = ""

            return responses

        # When specific countries are provided, query each explicitly
        logger.info(
            f"Starting partner extraction across {len(countries)} target countries: {countries}"
        )

        all_responses: list[dict[str, Any]] = []

        for country_idx, country_name in enumerate(countries, 1):
            # Resolve 2-letter country code (or pass through if already 2 letters)
            loc_code = COUNTRY_TO_LOCATION_CODE.get(
                country_name,
                country_name if len(country_name) == 2 else None,
            )

            logger.info(
                f"[{country_idx}/{len(countries)}] Extracting country: '{country_name}' (Location: {loc_code})"
            )
            print(
                f"\n[Extraction {country_idx}/{len(countries)}] Country: {country_name} (Code: {loc_code or 'Global'})"
            )

            responses = self.client.fetch_all_pages(
                location=loc_code,
                listing_type=listing_type,
                page_size=page_size,
            )

            # Tag each page response with the country label for downstream normalization
            for resp in responses:
                resp["_query_country"] = country_name

            all_responses.extend(responses)

        logger.info(
            f"Extraction completed: {len(all_responses)} total page responses collected"
        )
        return all_responses