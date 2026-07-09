import json

from typing import Any

from src.utils.logger import logger


class PartnerTransformation:

    def transform(
        self,
        raw_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        logger.info("Starting partner transformation")

        partners = []

        try:

            for response in raw_data:

                parsed = self._parse_response(response)

                partners.extend(parsed)

            logger.info(
                f"Extracted {len(partners)} partners"
            )

            return partners

        except Exception:

            logger.exception(
                "Partner transformation failed"
            )

            raise

    def _parse_response(
        self,
        response: dict[str, Any]
    ) -> list[dict[str, Any]]:

        return_value = response["data"]["returnValue"]

        if isinstance(return_value, str):
            return_value = json.loads(return_value)

        partners = return_value["results"]["partners"]

        return [
            self._flatten_partner(partner)
            for partner in partners
        ]

    def _flatten_partner(
        self,
        record: dict[str, Any]
    ) -> dict[str, Any]:

        partner = record.get("partner", {})

        return {

            "id": partner.get("Id", ""),

            "name": partner.get("Name", ""),

            "headquarters": partner.get(
                "Headquarters__c",
                "",
            ),

            "listing_url": partner.get(
                "AppExchange_Listing_URL__c",
                "",
            ),

            "logo_url": partner.get(
                "Logo_Image__c",
                "",
            ),

            "description": partner.get(
                "Description__c",
                "",
            ),

            "projects": partner.get(
                "Number_of_Projects__c",
                0,
            ),

            "credentials": partner.get(
                "Number_of_Credentials__c",
                0,
            ),

            "reviews": partner.get(
                "Review_Count__c",
                0,
            ),

            "rating": partner.get(
                "AppExchange_Rating__c",
                0,
            ),

            "weighted_rating": partner.get(
                "Weighted_Rating__c",
                0,
            ),

            "partner_score": partner.get(
                "PF_Total_Score__c",
                0,
            ),

            "diverse_owned": partner.get(
                "PF_Is_Diverse_Owned_Business__c",
                False,
            ),

            "pledge_1_percent": partner.get(
                "PF_Is_Pledge_1_Percent__c",
                False,
            ),

            "expertise": "; ".join(
                filter(
                    None,
                    [
                        item.get(
                            "Filter_Option__r",
                            {}
                        ).get(
                            "Name"
                        )
                        for item in record.get(
                            "expertises",
                            []
                        )
                    ],
                )
            ),

        }