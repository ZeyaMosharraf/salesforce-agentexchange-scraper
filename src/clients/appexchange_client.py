"""
AppExchange REST API Client.

Interacts with the AppExchange REST recommendations API endpoint:
https://api.appexchange.salesforce.com/recommendations/v3/listings

Supports cursor-based search pagination via `searchQueryId` (derived from
`searchQueryUid` on page 0) to extract full marketplace result sets.
"""

from typing import Any
import requests

from src.clients.base_client import BaseClient
from src.config import settings
from src.utils.logger import logger


class AppExchangeClient(BaseClient):
    """Client for querying the AppExchange recommendations REST API."""

    def __init__(self):
        self.session = self._create_session(allowed_methods=["GET"])
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://appexchange.salesforce.com",
            "Referer": "https://appexchange.salesforce.com/",
            "User-Agent": settings.user_agent,
        }

    def get_page(
        self,
        page: int = 0,
        page_size: int = 100,
        search_query_id: str | None = None,
        location: str | None = None,
        listing_type: str = "consultants",
    ) -> dict[str, Any]:
        """
        Fetches a single page of listings from recommendations/v3/listings.

        Args:
            page: 0-indexed page number.
            page_size: Number of listings per page (default 100).
            search_query_id: Cursor UID returned in searchQueryUid from page 0.
            location: Optional regional location filter (e.g. "US", "CA").
                      If None, fetches all records globally without filtering.
            listing_type: Listing category filter ("consultants", "apps", etc.).

        Returns:
            JSON response payload dictionary.
        """
        params: dict[str, Any] = {
            "type": listing_type,
            "pageSize": page_size,
            "page": page,
        }
        if location:
            params["location"] = location

        if search_query_id:
            params["searchQueryId"] = search_query_id

        try:
            response = self.session.get(
                url=settings.api_url,
                params=params,
                headers=self.headers,
                timeout=settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception(
                f"AppExchange API request failed for page {page} "
                f"(location={location}, query_id={search_query_id}): {e}"
            )
            raise

    def fetch_all_pages(
        self,
        location: str | None = None,
        listing_type: str = "consultants",
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extracts all listing pages using cursor-based pagination.
        If location is None, extracts all global records without geographic filter.

        Returns:
            List of raw page response dictionaries.
        """
        responses: list[dict[str, Any]] = []
        page = 0
        search_query_uid: str | None = None
        total_count: int | None = None
        total_fetched = 0

        loc_desc = location if location else "Global (All Locations)"
        logger.info(
            f"Starting AppExchange extraction for type='{listing_type}', location='{loc_desc}'"
        )
        print(f"\n[Extraction] Location: {loc_desc} | Type: {listing_type}")

        while True:
            if max_pages is not None and page >= max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break

            response = self.get_page(
                page=page,
                page_size=page_size,
                search_query_id=search_query_uid,
                location=location,
                listing_type=listing_type,
            )

            # Store response page
            responses.append(response)

            listings = response.get("listings", [])
            total_fetched += len(listings)

            if page == 0:
                search_query_uid = response.get("searchQueryUid")
                total_count = response.get("totalCount", 0)
                logger.info(
                    f"Page 0 returned searchQueryUid='{search_query_uid}', "
                    f"totalCount={total_count}"
                )

            print(
                f"\r  -> Page: {page} | Fetched: {total_fetched}/{total_count or '?'} listings",
                end="",
                flush=True,
            )

            # Termination conditions
            if not listings or (total_count is not None and total_fetched >= total_count):
                break

            page += 1

        print()
        logger.info(
            f"Extraction completed: {len(responses)} pages, {total_fetched} listings for location '{loc_desc}'"
        )
        return responses
