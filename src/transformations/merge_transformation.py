from typing import Any

from src.utils.logger import logger


def _derive_practice_size(employees_val: Any) -> str:
    """Calculates Salesforce practice size bracket from employee count."""
    if not employees_val:
        return ""
    try:
        emp = int(str(employees_val).strip())
        if emp <= 5:
            return "1-5"
        elif emp <= 20:
            return "6-20"
        elif emp <= 50:
            return "21-50"
        elif emp <= 100:
            return "51-100"
        else:
            return "100+"
    except ValueError:
        return str(employees_val)


class MergeTransformation:
    """
    Merges structured API partner records with enriched HTML listing details.
    Preserves API attributes and enriches with HTML metadata.
    """

    def transform(
        self,
        api_partner: dict[str, Any],
        html_partner: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            merged = api_partner.copy()

            for key, val in html_partner.items():
                if key == "description":
                    merged["html_description"] = val
                    if not merged.get("description") and val:
                        merged["description"] = (
                            "\n\n".join(val) if isinstance(val, list) else str(val)
                        )
                elif key == "statistics" and isinstance(val, dict):
                    stats = val.copy()
                    if not stats.get("rating") and api_partner.get("rating") is not None:
                        stats["rating"] = str(api_partner.get("rating"))
                    if (
                        not stats.get("review_count")
                        and api_partner.get("reviews") is not None
                    ):
                        stats["review_count"] = str(api_partner.get("reviews"))
                    if (
                        not stats.get("projects_completed")
                        and api_partner.get("projects") is not None
                    ):
                        stats["projects_completed"] = str(api_partner.get("projects"))
                    if (
                        not stats.get("certified_experts")
                        and api_partner.get("credentials") is not None
                    ):
                        stats["certified_experts"] = str(api_partner.get("credentials"))
                    merged["statistics"] = stats
                elif key == "contact" and isinstance(val, dict):
                    contact = val.copy()
                    if not contact.get("headquarters") and api_partner.get("headquarters"):
                        contact["headquarters"] = api_partner.get("headquarters")
                    merged["contact"] = contact
                elif key == "company" and isinstance(val, dict):
                    comp = val.copy()
                    if not comp.get("company_name") and api_partner.get("name"):
                        comp["company_name"] = api_partner.get("name")
                    merged["company"] = comp
                elif key == "reviews" and isinstance(val, list):
                    merged["html_reviews"] = val
                else:
                    merged[key] = val

            # Derive top-level columns for direct CSV and JSON filtering
            stats_dict = merged.get("statistics", {})
            contact_dict = merged.get("contact", {})
            company_dict = merged.get("company", {})
            geo_dict = merged.get("geographic", {})

            employees = str(stats_dict.get("employees", "") or "")
            merged["employees"] = employees

            # Practice Size: Prioritize filter query tag, fallback to HTML employee calculation
            if api_partner.get("practice_size"):
                merged["practice_size"] = api_partner["practice_size"]
            else:
                merged["practice_size"] = _derive_practice_size(employees)

            # Countries: Prioritize filter query tag, fallback to geographic/headquarters
            if api_partner.get("countries"):
                merged["countries"] = api_partner["countries"]
            else:
                geo_countries = geo_dict.get("countries", [])
                merged["countries"] = (
                    "; ".join(geo_countries)
                    if geo_countries
                    else merged.get("headquarters", "")
                )

            geo_states = geo_dict.get("states", [])
            merged["states"] = "; ".join(geo_states) if geo_states else ""

            # Top-level direct contact details
            merged["website"] = contact_dict.get("website", "")
            merged["email"] = contact_dict.get("email", "")
            merged["phone"] = contact_dict.get("phone", "")
            merged["founded_year"] = stats_dict.get("founded", "")
            merged["logo"] = company_dict.get("logo", "")

            return merged

        except Exception:
            logger.exception(f"Partner merge failed for '{api_partner.get('name', 'Unknown')}'")
            raise