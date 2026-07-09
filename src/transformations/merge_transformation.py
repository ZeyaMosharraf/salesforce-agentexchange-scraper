from typing import Any

from src.utils.logger import logger


class MergeTransformation:

    def transform(
        self,
        api_partner: dict[str, Any],
        html_partner: dict[str, Any],
    ) -> dict[str, Any]:

        logger.info(
            f"Merging partner: {api_partner.get('name', 'Unknown')}"
        )

        try:

            merged = api_partner.copy()

            merged.update(html_partner)

            return merged

        except Exception:

            logger.exception(
                "Partner merge failed"
            )

            raise