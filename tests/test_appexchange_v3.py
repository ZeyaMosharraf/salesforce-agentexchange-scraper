import unittest
from unittest.mock import MagicMock, patch

from src.clients.appexchange_v3_client import AppExchangeV3Client
from src.services.extraction_service import ExtractionService
from src.services.transformation_service import TransformationService
from src.transformations.appexchange_v3_transformation import (
    AppExchangeV3Transformation,
)


class TestAppExchangeV3(unittest.TestCase):

    def test_v3_client_cursor_pagination(self):
        """Test that AppExchangeV3Client correctly handles cursor pagination via searchQueryId."""
        client = AppExchangeV3Client()

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

    def test_v3_transformation_maps_and_preserves_zeros(self):
        """Test that AppExchangeV3Transformation maps attributes and preserves 0 and 0.0 values."""
        transformer = AppExchangeV3Transformation()
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
        # High Res Logo should be prioritized
        self.assertEqual(p["logo"], "https://example.com/logo_highres.png")

    def test_transformation_service_routes_modern_vs_legacy(self):
        """Test that TransformationService auto-routes to modern or legacy transformers."""
        service = TransformationService()

        modern_payload = [
            {
                "searchQueryUid": "uid-abc",
                "listings": [
                    {
                        "oafId": "a0N_modern_1",
                        "publisher": "Modern Partner",
                        "averageRating": 4.8,
                        "reviewsAmount": 15,
                    }
                ],
                "_data_source": "modern",
            }
        ]

        with patch.object(service.v3_transformation, "transform", return_value=[{"id": "a0N_modern_1", "name": "Modern Partner", "listing_url": ""}]) as mock_v3, \
             patch.object(service.partner_transformation, "transform") as mock_legacy:

            service.transform(modern_payload)
            mock_v3.assert_called_once()
            mock_legacy.assert_not_called()

    def test_extraction_service_strategy_selection(self):
        """Test that ExtractionService selects modern or legacy extractor based on settings."""
        service = ExtractionService()

        with patch.object(service, "_extract_modern", return_value=[{"modern": True}]) as mock_modern, \
             patch.object(service, "_extract_legacy", return_value=[{"legacy": True}]) as mock_legacy:

            # Test modern
            service.data_source = "modern"
            res = service.extract()
            self.assertEqual(res, [{"modern": True}])
            mock_modern.assert_called_once()
            mock_legacy.assert_not_called()

            mock_modern.reset_mock()
            mock_legacy.reset_mock()

            # Test legacy
            service.data_source = "legacy"
            res = service.extract()
            self.assertEqual(res, [{"legacy": True}])
            mock_legacy.assert_called_once()
            mock_modern.assert_not_called()


if __name__ == "__main__":
    unittest.main()

