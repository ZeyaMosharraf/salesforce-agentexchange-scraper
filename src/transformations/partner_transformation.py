import json
from typing import Any

from src.utils.logger import logger


class PartnerTransformation:

    def transform(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        logger.info("Starting partner transformation")
        partners = []

        try:
            for response in raw_data:
                parsed = self._parse_response(response)
                partners.extend(parsed)

            logger.info(
                f"Partner transformation: Extracted {len(partners)} partners"
            )
            return partners

        except Exception:
            logger.exception("Partner transformation failed")
            raise

    def _parse_response(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        return_value = response["returnValue"]
        if isinstance(return_value, str):
            return_value = json.loads(return_value)

        partners = return_value["results"]["partners"]
        return [self._flatten_partner(partner) for partner in partners]

    def _extract_options(self, items: Any) -> str:
        """Extract semicolon-separated option names from nested Salesforce relationship items."""
        if not isinstance(items, list):
            return ""
        names = [
            str(item.get("Filter_Option__r", {}).get("Name", "")).strip()
            for item in items
            if isinstance(item, dict) and item.get("Filter_Option__r", {}).get("Name")
        ]
        return "; ".join(filter(None, names))

    def _flatten_partner(self, record: dict[str, Any]) -> dict[str, Any]:
        p = record.get("partner", {})

        return {
            "id": p.get("Id", ""),
            "name": p.get("Name", ""),
            "country": record.get("_query_country", ""),
            "countries": "",
            "states": "",
            "practice_size": record.get("_query_practice_size", ""),
            "headquarters": p.get("Headquarters__c", ""),
            "website": "",
            "domain": "",
            "listing_url": p.get("AppExchange_Listing_URL__c", ""),
            "description": p.get("Description__c", ""),
            "projects": p.get("Number_of_Projects__c", 0),
            "credentials": p.get("Number_of_Credentials__c", 0),
            "reviews": p.get("Review_Count__c", 0),
            "rating": p.get("AppExchange_Rating__c", 0.0),
            "weighted_rating": p.get("Weighted_Rating__c", 0.0),
            "partner_score": p.get("PF_Total_Score__c", 0.0),
            "diverse_owned": p.get("PF_Is_Diverse_Owned_Business__c", False),
            "pledge_1_percent": p.get("PF_Is_Pledge_1_Percent__c", False),
            "expertise": self._extract_options(record.get("expertises")),
            "specializations": self._extract_options(record.get("specializations")),
            "cloud_expert_awards": self._extract_options(record.get("expertisesCloudExpert")),
            "cloud_accredited_awards": self._extract_options(record.get("expertisesCloudAccredited")),
        }