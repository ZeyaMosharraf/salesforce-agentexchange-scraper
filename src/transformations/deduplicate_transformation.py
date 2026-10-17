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
        seen_records: dict[str, dict[str, Any]] = {}

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

            if unique_key not in seen_records:
                partner_entry = partner.copy()
                seen_records[unique_key] = partner_entry
                unique_partners.append(partner_entry)
            else:
                # Merge multi-query metadata (e.g. partner found in both USA and Canada)
                existing = seen_records[unique_key]

                # Merge queried countries
                c_existing = [
                    c.strip()
                    for c in (existing.get("country") or "").split(";")
                    if c.strip()
                ]
                c_new = [
                    c.strip()
                    for c in (partner.get("country") or "").split(";")
                    if c.strip()
                ]
                merged_countries = list(dict.fromkeys(c_existing + c_new))
                if merged_countries:
                    existing["country"] = "; ".join(merged_countries)
                    existing["countries"] = "; ".join(merged_countries)

                # Merge practice sizes
                s_existing = [
                    s.strip()
                    for s in (existing.get("practice_size") or "").split(";")
                    if s.strip()
                ]
                s_new = [
                    s.strip()
                    for s in (partner.get("practice_size") or "").split(";")
                    if s.strip()
                ]
                merged_sizes = list(dict.fromkeys(s_existing + s_new))
                if merged_sizes:
                    existing["practice_size"] = "; ".join(merged_sizes)

                # Backfill any missing fields if the duplicate has them
                for field in [
                    "headquarters",
                    "description",
                    "expertise",
                    "specializations",
                    "cloud_expert_awards",
                    "cloud_accredited_awards",
                ]:
                    if not existing.get(field) and partner.get(field):
                        existing[field] = partner.get(field)

        duplicates_found = total_extracted - len(unique_partners)

        summary_msg = (
            f"Total Extracted: {total_extracted} | "
            f"Duplicates Exist: {duplicates_found} | "
            f"Unique Partners: {len(unique_partners)}"
        )

        logger.info(summary_msg)
        print(f"\n[Deduplication] {summary_msg}")

        return unique_partners

