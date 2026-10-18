import unittest
from unittest.mock import MagicMock, patch

from src.clients.appexchange_client import AppExchangeClient
from src.services.extraction_service import ExtractionService
from src.services.transformation_service import TransformationService
from src.transformations.appexchange_transformation import (
    AppExchangeTransformation,
)


class TestAppExchange(unittest.TestCase):

    def test_client_cursor_pagination(self):
        """Test that AppExchangeClient correctly handles cursor pagination via searchQueryId."""
        client = AppExchangeClient()

        page0_response = {
            "searchQueryUid": "test-uid-12345",
            "totalCount": 3,
            "listings": [
                {"oafId": "id-1", "title": "Listing 1", "publisher": "Company 1"},
                {"oafId": "id-2", "title": "Listing 2", "publisher": "Company 2"},
            ],
        }
        page1_response = {
            "totalCount": 3,
            "listings": [
                {"oafId": "id-3", "title": "Listing 3", "publisher": "Company 3"},
            ],
        }

        with patch.object(client, "get_page", side_effect=[page0_response, page1_response]) as mock_get_page:
            pages = client.fetch_all_pages(location="US", listing_type="consultants", page_size=2)

            self.assertEqual(len(pages), 2)
            self.assertEqual(mock_get_page.call_count, 2)

            # First call should have no search_query_id
            mock_get_page.assert_any_call(
                page=0,
                page_size=2,
                search_query_id=None,
                location="US",
                listing_type="consultants",
            )
            # Second call MUST include searchQueryId='test-uid-12345'
            mock_get_page.assert_any_call(
                page=1,
                page_size=2,
                search_query_id="test-uid-12345",
                location="US",
                listing_type="consultants",
            )

    def test_transformation_maps_and_preserves_zeros(self):
        """Test that AppExchangeTransformation maps attributes and preserves 0 and 0.0 values."""
        transformer = AppExchangeTransformation()
        raw_response = {
            "_query_country": "United States of America",
            "_query_practice_size": "",
            "listings": [
                {
                    "oafId": "a0N30000009xKzhEAE",
                    "publisher": "Coastal",
                    "title": "Coastal: #1 Salesforce Consulting",
                    "description": "Leading partner",
                    "averageRating": 0.0,
                    "reviewsAmount": 0,
                    "listingCategories": ["Agentforce", "Data Cloud"],
                    "logos": [
                        {"mediaId": "https://example.com/logo_small.png", "logoType": "Small Logo"},
                        {"mediaId": "https://example.com/logo_highres.png", "logoType": "High Res Logo"},
                    ],
                }
            ],
        }

        partners = transformer.transform([raw_response])
        self.assertEqual(len(partners), 1)
        p = partners[0]

        self.assertEqual(p["id"], "a0N30000009xKzhEAE")
        self.assertEqual(p["name"], "Coastal")
        self.assertEqual(p["title"], "Coastal: #1 Salesforce Consulting")
        self.assertEqual(p["listing_url"], "https://appexchange.salesforce.com/listingDetail?listingId=a0N30000009xKzhEAE")
        self.assertEqual(p["rating"], 0.0)
        self.assertEqual(p["reviews"], 0)
        self.assertEqual(p["country"], "United States of America")
        self.assertEqual(p["expertise"], "Agentforce; Data Cloud")
        self.assertEqual(p["logo"], "https://example.com/logo_highres.png")

    def test_multi_country_extraction_loop(self):
        """Test that ExtractionService iterates through multiple countries and maps location codes."""
        service = ExtractionService()

        with patch("src.services.extraction_service.filter_config") as mock_filter, \
             patch.object(service.client, "fetch_all_pages", return_value=[{"listings": []}]) as mock_fetch:

            mock_filter.countries = ["United States of America", "Canada"]
            mock_filter.listing_type = "consultants"
            mock_filter.page_size = 100

            responses = service.extract()

            self.assertEqual(len(responses), 2)
            self.assertEqual(mock_fetch.call_count, 2)

            # Check US call
            mock_fetch.assert_any_call(
                location="US",
                listing_type="consultants",
                page_size=100,
            )
            # Check Canada call
            mock_fetch.assert_any_call(
                location="CA",
                listing_type="consultants",
                page_size=100,
            )

    def test_global_extraction_when_countries_empty(self):
        """Test that ExtractionService passes location=None when countries is empty (global extraction)."""
        service = ExtractionService()

        with patch("src.services.extraction_service.filter_config") as mock_filter, \
             patch.object(service.client, "fetch_all_pages", return_value=[{"listings": []}]) as mock_fetch:

            mock_filter.countries = []
            mock_filter.listing_type = "consultants"
            mock_filter.page_size = 100

            responses = service.extract()

            self.assertEqual(len(responses), 1)
            mock_fetch.assert_called_once_with(
                location=None,
                listing_type="consultants",
                page_size=100,
            )


if __name__ == "__main__":
    unittest.main()

