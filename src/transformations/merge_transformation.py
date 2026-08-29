import re
from typing import Any

from src.config import CA_PROVINCES, US_STATES
from src.utils.logger import logger


def _parse_headquarters_country(hq_text: str) -> tuple[str, str]:
    """
    Parses the primary headquarters country and state from raw location string.
    Returns (Country, State).
    """
    if not hq_text or not hq_text.strip():
        return "", ""

    text = hq_text.strip()

    # Check for US mentions
    us_match = re.search(
        r"\b(USA|U\.S\.A\.|United States of America|United States|U\.S\.|US)\b",
        text,
        re.I,
    )

    found_state = ""
    for code, name in US_STATES.items():
        if re.search(rf"\b{code}\b", text) or re.search(rf"\b{name}\b", text, re.I):
            found_state = name
            break

    if found_state or us_match:
        return "United States of America", found_state

    # Canadian provinces
    found_province = ""
    for code, name in CA_PROVINCES.items():
        if re.search(rf"\b{code}\b", text) or re.search(rf"\b{name}\b", text, re.I):
            found_province = name
            break

    if found_province or re.search(r"\bCanada\b", text, re.I):
        return "Canada", found_province

    if re.search(r"\b(UK|U\.K\.|United Kingdom|England|Scotland|Wales|London)\b", text, re.I):
        return "United Kingdom", ""
    if re.search(r"\b(India)\b", text, re.I):
        return "India", ""
    if re.search(r"\b(Germany|Deutschland)\b", text, re.I):
        return "Germany", ""
    if re.search(r"\b(Australia)\b", text, re.I):
        return "Australia", ""
    if re.search(r"\b(France)\b", text, re.I):
        return "France", ""
    if re.search(r"\b(Netherlands|Holland)\b", text, re.I):
        return "Netherlands", ""

    parts = [p.strip() for p in text.split(",") if p.strip()]
    if parts:
        return parts[-1], ""

    return text, ""


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
                    field_map = {
                        "rating": "rating",
                        "review_count": "reviews",
                        "projects_completed": "projects",
                        "certified_experts": "credentials",
                    }
                    for stat_k, api_k in field_map.items():
                        if not stats.get(stat_k) and api_partner.get(api_k) is not None:
                            stats[stat_k] = str(api_partner[api_k])
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

            # Extract component dictionaries
            stats_dict = merged.get("statistics", {})
            contact_dict = merged.get("contact", {})
            company_dict = merged.get("company", {})
            geo_dict = merged.get("geographic", {})
            comp_dict = html_partner.get("competencies", {})

            employees = str(stats_dict.get("employees", "") or "")

            # 1. Primary Headquarters Country & State
            raw_hq = contact_dict.get("headquarters", "") or api_partner.get("headquarters", "")
            hq_country, hq_state = _parse_headquarters_country(raw_hq)
            country = api_partner.get("country") or api_partner.get("countries") or hq_country

            # 2. Operating & Served Countries (Geographic Focus)
            geo_countries = geo_dict.get("countries", [])
            countries = "; ".join(geo_countries) if geo_countries else country

            # 3. Operating & Served States
            geo_states = geo_dict.get("states", [])
            states = "; ".join(geo_states) if geo_states else hq_state

            # 4. Supported Languages
            raw_lang = html_partner.get("languages", [])
            languages = "; ".join(raw_lang) if isinstance(raw_lang, list) else str(raw_lang)

            # 5. Industry & Product Competencies
            raw_industry = comp_dict.get("industry_competencies", [])
            industry_competencies = (
                "; ".join(raw_industry) if isinstance(raw_industry, list) else str(raw_industry)
            )

            raw_product = comp_dict.get("product_competencies", [])
            product_competencies = (
                "; ".join(raw_product) if isinstance(raw_product, list) else str(raw_product)
            )

            # Structured, perfectly ordered partner dictionary
            ordered_partner = {
                "id": api_partner.get("id", ""),
                "name": api_partner.get("name", ""),
                "country": country,
                "countries": countries,
                "states": states,
                "languages": languages,
                "practice_size": api_partner.get("practice_size", ""),
                "employees": employees,
                "headquarters": raw_hq,
                "industry_competencies": industry_competencies,
                "product_competencies": product_competencies,
                "expertise": api_partner.get("expertise", ""),
                "specializations": api_partner.get("specializations", ""),
                "cloud_expert_awards": api_partner.get("cloud_expert_awards", ""),
                "cloud_accredited_awards": api_partner.get("cloud_accredited_awards", ""),
                "website": contact_dict.get("website", ""),
                "domain": contact_dict.get("domain", ""),
                "email": contact_dict.get("email", ""),
                "phone": contact_dict.get("phone", ""),
                "founded_year": stats_dict.get("founded", ""),
                "logo": company_dict.get("logo", ""),
                "rating": api_partner.get("rating", 0.0),
                "reviews": api_partner.get("reviews", 0),
                "projects": api_partner.get("projects", 0),
                "credentials": api_partner.get("credentials", 0),
                "partner_score": api_partner.get("partner_score", 0.0),
                "diverse_owned": api_partner.get("diverse_owned", False),
                "pledge_1_percent": api_partner.get("pledge_1_percent", False),
                "listing_url": api_partner.get("listing_url", ""),
                "description": api_partner.get("description", ""),
                "html_status": merged.get("html_status", "Success"),
            }

            # Append any remaining nested objects (metadata, about, overview, etc.)
            for k, v in merged.items():
                if k not in ordered_partner:
                    ordered_partner[k] = v

            return ordered_partner

        except Exception:
            logger.exception(f"Partner merge failed for '{api_partner.get('name', 'Unknown')}'")
            raise