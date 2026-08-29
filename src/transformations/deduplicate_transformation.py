from typing import Any

from src.utils.logger import logger


class DeduplicateTransformation:
    """
    Identifies and removes duplicate partner records from extracted data.
    Strictly handles deduplication without altering or merging partner fields.
    """

    def transform(self, partners: list[dict[str, Any]]) -> list[dict[str, Any]]:
        total_extracted = len(partners)
        unique_partners: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        for partner in partners:
            unique_key = (
                partner.get("id")
                or partner.get("listing_url")
                or (
                    partner.get("name", "").strip().lower()
                    if partner.get("name")
                    else None
                )
            )

            if not unique_key:
                unique_partners.append(partner)
                continue

            if unique_key not in seen_keys:
                seen_keys.add(unique_key)
                unique_partners.append(partner)

        duplicates_found = total_extracted - len(unique_partners)

        summary_msg = (
            f"Total Extracted: {total_extracted} | "
            f"Duplicates Exist: {duplicates_found} | "
            f"Unique Partners: {len(unique_partners)}"
        )

        logger.info(summary_msg)
        print(f"\n[Deduplication] {summary_msg}")

        return unique_partners
