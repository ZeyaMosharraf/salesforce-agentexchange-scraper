"""
AppExchange REST API Data Transformation.

Normalizes raw JSON responses from recommendations/v3/listings into the
standardized partner dictionary format expected by the downstream deduplication,
HTML enrichment, and export pipelines.
"""

from typing import Any

from src.utils.logger import logger


class AppExchangeTransformation:
    """Transforms raw AppExchange recommendations API responses into partner dictionaries."""

    def transform(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Parses a list of page responses and returns a list of flattened partner dictionaries.
        """
        logger.info("Starting AppExchange transformation")
        partners = []

        try:
            for response in raw_data:
                parsed = self._parse_response(response)
                partners.extend(parsed)

            logger.info(
                f"AppExchange transformation: Extracted {len(partners)} partner listings"
            )
            return partners

        except Exception:
            logger.exception("AppExchange transformation failed")
            raise

    def _parse_response(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        listings = response.get("listings", [])
        query_country = response.get("_query_country", "United States of America")
        query_size = response.get("_query_practice_size", "")

        return [
            self._flatten_listing(listing, query_country, query_size)
            for listing in listings
        ]

    def _extract_logo(self, logos: Any) -> str:
        """Extract best available logo URL from logos array."""
        if not isinstance(logos, list) or not logos:
            return ""

        preferred_types = ["High Res Logo", "Logo", "Big Logo", "High Res Svg"]
        for pref in preferred_types:
            for logo in logos:
                if isinstance(logo, dict) and logo.get("logoType") == pref:
                    media_id = logo.get("mediaId")
                    if media_id:
                        return str(media_id).strip()

        for logo in logos:
            if isinstance(logo, dict) and logo.get("mediaId"):
                return str(logo["mediaId"]).strip()

        return ""

    def _flatten_listing(
        self,
        listing: dict[str, Any],
        query_country: str,
        query_size: str,
    ) -> dict[str, Any]:
        oaf_id = str(listing.get("oafId") or "").strip()
        publisher = str(listing.get("publisher") or "").strip()
        title = str(listing.get("title") or "").strip()
        name = publisher or title

        # Construct official AppExchange listing detail URL
        listing_url = (
            f"https://appexchange.salesforce.com/listingDetail?listingId={oaf_id}"
            if oaf_id
            else ""
        )

        avg_rating = listing.get("averageRating")
        rating = float(avg_rating) if avg_rating is not None else 0.0

        reviews_amt = listing.get("reviewsAmount")
        reviews = int(reviews_amt) if reviews_amt is not None else 0

        categories = listing.get("listingCategories", [])
        expertise = (
            "; ".join(str(c) for c in categories if c)
            if isinstance(categories, list)
            else ""
        )

        logo_url = self._extract_logo(listing.get("logos"))

        return {
            "id": oaf_id,
            "name": name,
            "title": title,
            "country": query_country,
            "countries": "",
            "states": "",
            "practice_size": query_size,
            "headquarters": "",
            "website": "",
            "domain": "",
            "listing_url": listing_url,
            "description": str(listing.get("description") or "").strip(),
            "projects": 0,
            "credentials": 0,
            "reviews": reviews,
            "rating": rating,
            "weighted_rating": 0.0,
            "partner_score": 0.0,
            "diverse_owned": False,
            "pledge_1_percent": False,
            "expertise": expertise,
            "specializations": "",
            "cloud_expert_awards": "",
            "cloud_accredited_awards": "",
            "logo": logo_url,
        }

