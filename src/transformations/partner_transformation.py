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

    def _flatten_partner(self, record: dict[str, Any]) -> dict[str, Any]:
        p = record.get("partner", {})

        # Query metadata tagged during extraction loop
        query_country = record.get("_query_country", "")
        query_practice_size = record.get("_query_practice_size", "")

        # Extract expertises
        expertises = [
            item.get("Filter_Option__r", {}).get("Name")
            for item in record.get("expertises", [])
            if item.get("Filter_Option__r", {}).get("Name")
        ]

        # Extract specializations
        specializations = [
            item.get("Filter_Option__r", {}).get("Name")
            for item in record.get("specializations", [])
            if item.get("Filter_Option__r", {}).get("Name")
        ]

        # Extract cloud expert awards
        cloud_experts = [
            item.get("Filter_Option__r", {}).get("Name")
            for item in record.get("expertisesCloudExpert", [])
            if item.get("Filter_Option__r", {}).get("Name")
        ]

        # Extract cloud accredited awards
        cloud_accredited = [
            item.get("Filter_Option__r", {}).get("Name")
            for item in record.get("expertisesCloudAccredited", [])
            if item.get("Filter_Option__r", {}).get("Name")
        ]

        return {
            "id": p.get("Id", ""),
            "name": p.get("Name", ""),
            "headquarters": p.get("Headquarters__c", ""),
            "countries": query_country,
            "practice_size": query_practice_size,
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
            "expertise": "; ".join(filter(None, expertises)),
            "specializations": "; ".join(filter(None, specializations)),
            "cloud_expert_awards": "; ".join(filter(None, cloud_experts)),
            "cloud_accredited_awards": "; ".join(filter(None, cloud_accredited)),
        }