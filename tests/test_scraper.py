import threading
import unittest
from unittest.mock import MagicMock, patch

from src.clients.html_client import HtmlClient
from src.services.transformation_service import TransformationService
from src.transformations.deduplicate_transformation import DeduplicateTransformation
from src.transformations.html_transformation import HtmlTransformation


class TestScraperFixes(unittest.TestCase):

    def test_thread_local_sessions(self):
        """Test that each thread receives its own requests.Session instance."""
        client = HtmlClient()
        sessions = []

        def worker():
            sessions.append(client.session)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 5 sessions should be distinct object instances
        self.assertEqual(len(sessions), 5)
        self.assertEqual(len(set(id(s) for s in sessions)), 5)

    def test_404_preserves_full_schema(self):
        """Test that partners with 404 HTML still get full merged schema with 31 keys."""
        service = TransformationService()
        sample_partner = {
            "id": "a7f3m000000PTxrAAG",
            "name": "Ascend Technologies",
            "country": "United States of America",
            "countries": "",
            "states": "",
            "practice_size": "1-5",
            "headquarters": "Chicago, IL",
            "website": "",
            "domain": "",
            "listing_url": "https://appexchange.salesforce.com/appxConsultingListingDetail?listingId=a0N3u00000MBkqUEAT",
            "description": "Sample description",
            "projects": 25,
            "credentials": 38,
            "reviews": 10,
            "rating": 4.93,
            "weighted_rating": 0.0,
            "partner_score": 1190.8,
            "diverse_owned": False,
            "pledge_1_percent": False,
            "expertise": "Agentforce",
            "specializations": "Healthcare",
            "cloud_expert_awards": "",
            "cloud_accredited_awards": "",
        }

        # Mock html_client.get to return None (simulate 404)
        with patch.object(service.html_client, "get", return_value=None):
            result = service.process_partner(sample_partner)

        self.assertEqual(result["html_status"], "Not Found")
        # Ensure schema keys are present and not missing
        self.assertIn("languages", result)
        self.assertIn("employees", result)
        self.assertIn("industry_competencies", result)
        self.assertIn("product_competencies", result)
        self.assertIn("founded_year", result)
        # Check that headquarters was parsed
        self.assertEqual(result["country"], "United States of America")
        self.assertEqual(result["states"], "Illinois")

    def test_deduplication_merges_countries_and_sizes(self):
        """Test that duplicates across countries are merged rather than discarded."""
        dedup = DeduplicateTransformation()
        partners = [
            {
                "id": "001",
                "name": "Global Consulting",
                "country": "United States of America",
                "practice_size": "1-5",
                "headquarters": "New York, NY",
            },
            {
                "id": "001",
                "name": "Global Consulting",
                "country": "Canada",
                "practice_size": "6-20",
                "headquarters": "New York, NY",
            },
        ]

        unique = dedup.transform(partners)
        self.assertEqual(len(unique), 1)
        self.assertEqual(
            unique[0]["country"], "United States of America; Canada"
        )
        self.assertEqual(unique[0]["practice_size"], "1-5; 6-20")

    def test_zero_projects_preserved_in_statistics(self):
        """Test that numeric 0 in consultant extensions is preserved as '0'."""
        html_trans = HtmlTransformation()
        listing = {
            "listing/extensions/consultant/listings/Listing": {
                "projectsCompleted": 0,
                "certifiedExperts": 0,
            }
        }
        publisher = {"yearFounded": 2020, "employees": 5}
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<html></html>", "lxml")
        stats = html_trans._parse_statistics(soup, listing, publisher)

        self.assertEqual(stats["projects_completed"], "0")
        self.assertEqual(stats["certified_experts"], "0")
        self.assertEqual(stats["founded"], "2020")
        self.assertEqual(stats["employees"], "5")


if __name__ == "__main__":
    unittest.main()

