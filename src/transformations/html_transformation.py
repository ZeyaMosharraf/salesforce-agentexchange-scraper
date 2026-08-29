import json
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from src.config import LANGUAGE_MAP
from src.utils.logger import logger


class HtmlTransformation:
    """
    Transforms raw HTML from Salesforce AppExchange listing pages into structured partner data.

    Uses a multi-layered extraction strategy:
    1. Primary: Extracts embedded `window.stores` state JSON containing full partner listing,
       publisher details, ratings, reviews, employees, and media plugins.
    2. Secondary: Extracts Schema.org JSON-LD structured metadata.
    3. Tertiary: Fallback to BeautifulSoup DOM selector parsing for static HTML tags.
    """

    def transform(self, html: str) -> dict[str, Any]:
        try:
            soup = BeautifulSoup(html, "lxml")
            stores = self._extract_stores(soup)
            listing = stores.get("LISTING", {}).get("listing", {})
            publisher = listing.get("publisher", {})
            ld_json = self._extract_ld_json(soup)

            return {
                "metadata": self._parse_metadata(soup, listing, ld_json),
                "company": self._parse_company(soup, listing, publisher),
                "statistics": self._parse_statistics(soup, listing, publisher),
                "resources": self._parse_resources(soup, listing),
                "reviews": self._parse_reviews(soup, listing),
                "links": self._parse_links(soup, publisher),
                "languages": self._parse_languages(soup, listing),
                "user_action": self._parse_user_actions(soup, listing),
                "geographic": self._parse_geographic_focus(soup, listing, publisher),
                "competencies": self._parse_competencies(soup, listing),
                "contact": self._parse_contact(soup, listing, publisher),
                "about": self._parse_about(soup, publisher),
                "description": self._parse_description(soup, listing, publisher),
                "highlight": self._parse_highlights(soup, listing),
                "overview": self._parse_overview(soup, listing, publisher),
            }

        except Exception:
            logger.exception("HTML transformation failed")
            raise

    # ============================================================
    # STORE & JSON-LD EXTRACTION
    # ============================================================

    def _extract_stores(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extracts the embedded window.stores JSON state from page scripts."""
        for script in soup.find_all("script"):
            content = script.string or script.get_text() or ""
            if "window.stores=" in content:
                idx = content.find("window.stores=") + len("window.stores=")
                try:
                    stores, _ = json.JSONDecoder().raw_decode(content[idx:])
                    if isinstance(stores, dict):
                        return stores
                except Exception:
                    pass
        return {}

    def _extract_ld_json(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extracts JSON-LD structured data elements from script tags."""
        items: list[dict[str, Any]] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or script.get_text() or "")
                if isinstance(data, list):
                    items.extend(data)
                elif isinstance(data, dict):
                    items.append(data)
            except Exception:
                pass
        return items

    # ============================================================
    # REUSABLE HELPER FUNCTIONS
    # ============================================================

    def _clean(self, text: Any) -> str:
        """Clean extracted text from any input type safely."""
        if text is None:
            return ""
        if isinstance(text, (list, tuple)):
            text = " ".join(str(t) for t in text)
        return re.sub(r"\s+", " ", str(text)).strip()

    def _safe_text(self, element: Any) -> str:
        """Safely return cleaned text from a Tag or string."""
        if element is None:
            return ""
        if hasattr(element, "get_text"):
            return self._clean(element.get_text(" ", strip=True))
        return self._clean(element)

    def _safe_attr(self, element: Any, attr: str) -> str:
        """Safely return attribute value from a Tag."""
        if element is None:
            return ""
        val = element.get(attr, "")
        return self._clean(val)

    def _first_existing(self, node: Any, selectors: list[str]) -> Any:
        """Return first matching selector from a BeautifulSoup or Tag node."""
        if node is None:
            return None
        for selector in selectors:
            found = node.select_one(selector)
            if found is not None:
                return found
        return None

    def _extract_names(self, items: Any, key: str = "name", max_len: int = 60) -> list[str]:
        """Reusable extractor for lists of strings or dicts with a given key."""
        if not isinstance(items, list):
            return []
        result: list[str] = []
        for item in items:
            if isinstance(item, str) and item.strip() and len(item.strip()) < max_len:
                result.append(item.strip())
            elif isinstance(item, dict) and item.get(key):
                val = str(item.get(key)).strip()
                if val and len(val) < max_len:
                    result.append(val)
        return list(dict.fromkeys(result))

    def _parse_bullet_text(self, node: Any, max_len: int = 60) -> list[str]:
        """Reusable extractor for text nodes separated by bullets or commas."""
        if node is None:
            return []
        text = self._safe_text(node)
        if "•" in text:
            return [p.strip() for p in text.split("•") if p.strip() and len(p.strip()) < max_len]
        elif "," in text:
            return [p.strip() for p in text.split(",") if p.strip() and len(p.strip()) < max_len]
        elif text and len(text) < max_len:
            return [text]
        return []

    # ============================================================
    # METADATA
    # ============================================================

    def _parse_metadata(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        ld_json: list[dict[str, Any]],
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "title": self._safe_text(soup.find("title"))
            or str(listing.get("seoTitle") or listing.get("name") or ""),
            "canonical": self._safe_attr(
                soup.select_one("link[rel='canonical']"), "href"
            ),
            "description": self._safe_attr(
                soup.select_one("meta[name='description']"), "content"
            )
            or str(listing.get("description") or ""),
            "keywords": self._safe_attr(
                soup.select_one("meta[name='keywords']"), "content"
            ),
            "robots": self._safe_attr(
                soup.select_one("meta[name='robots']"), "content"
            ),
            "language": self._safe_attr(soup.select_one("html"), "lang") or "en",
            "og": {},
            "twitter": {},
        }

        for meta in soup.select("meta[property^='og:']"):
            raw_prop = meta.get("property")
            if raw_prop:
                prop_str = str(raw_prop[0] if isinstance(raw_prop, list) else raw_prop)
                key = prop_str.replace("og:", "")
                metadata["og"][key] = self._clean(meta.get("content"))

        for meta in soup.select("meta[name^='twitter:']"):
            raw_name = meta.get("name")
            if raw_name:
                name_str = str(raw_name[0] if isinstance(raw_name, list) else raw_name)
                key = name_str.replace("twitter:", "")
                metadata["twitter"][key] = self._clean(meta.get("content"))

        return metadata

    # ============================================================
    # COMPANY INFORMATION
    # ============================================================

    def _parse_company(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        publisher: dict[str, Any],
    ) -> dict[str, Any]:
        name = (
            str(publisher.get("name") or "")
            or str(listing.get("name") or "")
            or self._safe_text(
                self._first_existing(
                    soup,
                    ["h1", ".appx-listing-title", ".listing-title", ".appx-title"],
                )
            )
        )

        # Logo extraction
        logo = ""
        pub_logo = publisher.get("publisher/plugins/PublisherLogo", {})
        if isinstance(pub_logo, dict) and pub_logo.get("Logo"):
            logo = str(pub_logo.get("Logo"))
        elif isinstance(pub_logo, dict) and pub_logo.get("items"):
            items = pub_logo.get("items", [])
            if items and isinstance(items[0], dict):
                logo = str(items[0].get("mediaId", ""))
        if not logo:
            logo = self._safe_attr(
                self._first_existing(
                    soup,
                    [
                        ".appx-logo img",
                        ".listing-logo img",
                        ".partner-logo img",
                        "img.appx-logo",
                    ],
                ),
                "src",
            )
        if not logo:
            logo = self._safe_attr(
                soup.select_one("meta[property='og:image']"), "content"
            )

        # Banner extraction
        banner = ""
        carousel = listing.get("listing/plugins/Carousel", {})
        if isinstance(carousel, dict) and carousel.get("items"):
            items = carousel.get("items", [])
            if items and isinstance(items[0], dict):
                banner = str(items[0].get("data", {}).get("url", ""))
        if not banner:
            banner = self._safe_attr(
                self._first_existing(soup, [".hero img", ".banner img", ".overview img"]),
                "src",
            )

        # Tagline extraction
        tagline = str(listing.get("tagline") or "")
        if not tagline and listing.get("description"):
            tagline = str(listing.get("description"))
        elif not tagline and publisher.get("description"):
            desc = str(publisher.get("description", ""))
            first_line = desc.split("\n")[0].strip()
            tagline = first_line[:150]
        if not tagline:
            overview_node = soup.select_one(".appx-multi-line-fixed")
            if overview_node is not None:
                tagline = self._safe_text(overview_node).split(".")[0]

        return {
            "company_name": self._clean(name),
            "logo": self._clean(logo),
            "banner": self._clean(banner),
            "tagline": self._clean(tagline),
        }

    # ============================================================
    # STATISTICS
    # ============================================================

    def _parse_statistics(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        publisher: dict[str, Any],
    ) -> dict[str, Any]:
        reviews_summary = listing.get("reviewsSummary", {})
        consultant_ext = listing.get(
            "listing/extensions/consultant/listings/Listing", {}
        )

        rating = ""
        review_count = ""
        if isinstance(reviews_summary, dict) and reviews_summary.get("averageRating") is not None:
            rating = str(reviews_summary.get("averageRating"))
        elif listing.get("rating") is not None:
            rating = str(listing.get("rating"))

        if isinstance(reviews_summary, dict) and reviews_summary.get("reviewCount") is not None:
            review_count = str(reviews_summary.get("reviewCount"))
        elif listing.get("reviewCount") is not None:
            review_count = str(listing.get("reviewCount"))

        projects_completed = str(consultant_ext.get("projectsCompleted", "") or "") if isinstance(consultant_ext, dict) else ""
        certified_experts = str(consultant_ext.get("certifiedExperts", "") or "") if isinstance(consultant_ext, dict) else ""
        founded = str(publisher.get("yearFounded", "") or "")
        employees = str(publisher.get("employees", "") or "")

        # Fallback to text searching if empty
        if not (rating or review_count or projects_completed or certified_experts or founded or employees):
            text = soup.get_text(" ", strip=True)
            r_match = re.search(r"([0-5]\.\d+)", text)
            if r_match:
                rating = r_match.group(1)
            rev_match = re.search(r"(\d+)\s+Reviews?", text, re.I)
            if rev_match:
                review_count = rev_match.group(1)
            proj_match = re.search(r"(\d+)\s+Projects", text, re.I)
            if proj_match:
                projects_completed = proj_match.group(1)
            exp_match = re.search(r"(\d+)\s+Certified", text, re.I)
            if exp_match:
                certified_experts = exp_match.group(1)
            f_match = re.search(r"Founded\s*(\d{4})", text, re.I)
            if f_match:
                founded = f_match.group(1)

        return {
            "rating": rating,
            "review_count": review_count,
            "projects_completed": projects_completed,
            "certified_experts": certified_experts,
            "founded": founded,
            "employees": employees,
        }

    # ============================================================
    # RESOURCES
    # ============================================================

    def _parse_resources(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
    ) -> list[dict[str, Any]]:
        resources: list[dict[str, Any]] = []

        content_plugin = listing.get("listing/plugins/Content", {})
        if isinstance(content_plugin, dict) and content_plugin.get("items"):
            for item in content_plugin.get("items", []):
                if isinstance(item, dict):
                    idata = item.get("data", {})
                    if isinstance(idata, dict) and idata.get("url"):
                        resources.append({
                            "title": self._clean(idata.get("title", "")),
                            "url": str(idata.get("url", "")),
                            "type": str(idata.get("type", "Resource")),
                        })

        for link in soup.find_all("a", href=True):
            href = self._clean(link.get("href"))
            title = self._safe_text(link)
            if href and any(
                ext in href.lower()
                for ext in [".pdf", "whitepaper", "datasheet", "case-study", "guide", "ebook"]
            ):
                if not any(r["url"] == href for r in resources):
                    resources.append({
                        "title": title or "Document Resource",
                        "url": href,
                        "type": "Document",
                    })

        return resources

    # ============================================================
    # REVIEWS
    # ============================================================

    def _parse_reviews(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
    ) -> list[dict[str, Any]]:
        reviews: list[dict[str, Any]] = []
        reviews_summary = listing.get("reviewsSummary", {})
        if isinstance(reviews_summary, dict) and reviews_summary:
            reviews.append({
                "rating": str(reviews_summary.get("averageRating", "")),
                "review_count": str(reviews_summary.get("reviewCount", "")),
                "id": str(reviews_summary.get("id", "")),
            })

        for block in soup.select(".review, .appx-review, .review-item"):
            review = {
                "reviewer": self._safe_text(
                    self._first_existing(
                        block, [".reviewer", ".author", ".review-author", ".name"]
                    )
                ),
                "rating": self._safe_text(
                    self._first_existing(
                        block, [".rating", ".stars", ".review-rating"]
                    )
                ),
                "date": self._safe_text(
                    self._first_existing(block, [".date", ".review-date"])
                ),
                "review": self._safe_text(
                    self._first_existing(
                        block, [".content", ".review-text", ".review-body"]
                    )
                ),
            }
            if any(review.values()):
                reviews.append(review)

        return reviews

    # ============================================================
    # LINKS
    # ============================================================

    def _parse_links(
        self,
        soup: BeautifulSoup,
        publisher: dict[str, Any],
    ) -> dict[str, list[str]]:
        internal: list[str] = []
        external: list[str] = []
        mailto: list[str] = []
        telephone: list[str] = []

        if publisher.get("website"):
            external.append(str(publisher.get("website")))
        if publisher.get("email"):
            mailto.append(str(publisher.get("email")))
        if publisher.get("phone"):
            telephone.append(str(publisher.get("phone")))

        for a in soup.find_all("a", href=True):
            href = self._clean(a.get("href"))
            if not href:
                continue
            if href.startswith("mailto:"):
                mailto.append(href.replace("mailto:", ""))
            elif href.startswith("tel:"):
                telephone.append(href.replace("tel:", ""))
            elif href.startswith("http"):
                external.append(href)
            else:
                internal.append(href)

        return {
            "internal": list(dict.fromkeys(internal)),
            "external": list(dict.fromkeys(external)),
            "mailto": list(dict.fromkeys(mailto)),
            "telephone": list(dict.fromkeys(telephone)),
        }

    # ============================================================
    # LANGUAGES (SUPPORTED LANGUAGES)
    # ============================================================

    def _parse_languages(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
    ) -> list[str]:
        languages: list[str] = []

        # 1. State JSON: listing/extensions/consultant/listings/Listing.languages
        consultant_ext = listing.get(
            "listing/extensions/consultant/listings/Listing", {}
        )
        if isinstance(consultant_ext, dict):
            for code in consultant_ext.get("languages", []):
                code_str = str(code).strip()
                languages.append(LANGUAGE_MAP.get(code_str.lower(), code_str))

        if not languages:
            for ext in listing.get("extensions", []):
                if isinstance(ext, dict):
                    ext_data = ext.get("data", {})
                    if isinstance(ext_data, dict):
                        for code in ext_data.get("languages", []):
                            code_str = str(code).strip()
                            languages.append(LANGUAGE_MAP.get(code_str.lower(), code_str))

        # 2. DOM Selector fallback
        if not languages:
            node = (
                soup.select_one('[data-testid="languages-section"] p')
                or soup.select_one('.languages-container p')
                or soup.select_one('[data-testid="supported-languages"]')
            )
            languages = self._parse_bullet_text(node, max_len=40)

        if not languages:
            languages.append("English")

        return list(dict.fromkeys(languages))

    # ============================================================
    # APPX USER ACTIONS
    # ============================================================

    def _parse_user_actions(self, soup: BeautifulSoup, listing: dict[str, Any]) -> dict[str, Any]:
        lead_info = listing.get("listing/plugins/LeadTrialInformation", {})
        learn_more = ""
        if isinstance(lead_info, dict):
            learn_more = str(lead_info.get("learnMoreUrl") or "")

        if not learn_more:
            for script in soup.find_all("script"):
                script_text = script.get_text()
                if "learnMoreUrl" in script_text:
                    match = re.search(r"learnMoreUrl\s*:\s*['\"]([^'\"]+)['\"]", script_text)
                    if match:
                        learn_more = match.group(1)
                        break

        return {"learn_more_url": learn_more}

    # ============================================================
    # GEOGRAPHIC FOCUS (OPERATING & SERVED COUNTRIES)
    # ============================================================

    def _parse_geographic_focus(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        publisher: dict[str, Any],
    ) -> dict[str, Any]:
        countries: list[str] = []
        states: list[str] = []

        # 1. State JSON: consultantLocations
        locs = listing.get("consultantLocations", {})
        if isinstance(locs, dict):
            countries.extend(self._extract_names(locs.get("locations"), key="countryName"))
            countries.extend(self._extract_names(locs.get("countries"), key="name"))
            states.extend(self._extract_names(locs.get("states"), key="name"))

        # 2. DOM Selector for countries
        if not countries:
            node = (
                soup.select_one('[data-testid="geographic-focus-countries"]')
                or soup.select_one('.countries-container p.section-text')
            )
            countries = self._parse_bullet_text(node, max_len=60)

        # 3. DOM Selector for states
        if not states:
            node = (
                soup.select_one('[data-testid="geographic-focus-states"]')
                or soup.select_one('.states-container p.section-text')
            )
            states = self._parse_bullet_text(node, max_len=60)

        return {
            "countries": list(dict.fromkeys(countries)),
            "states": list(dict.fromkeys(states)),
        }

    # ============================================================
    # COMPETENCIES (INDUSTRY & PRODUCT COMPETENCIES)
    # ============================================================

    def _parse_competencies(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
    ) -> dict[str, list[str]]:
        comp = listing.get("consultantCompetencies", {})
        industry = self._extract_names(comp.get("industryCompetencies") if isinstance(comp, dict) else [])
        product = self._extract_names(comp.get("productCompetencies") if isinstance(comp, dict) else [])

        # DOM Fallbacks
        if not industry:
            node = self._first_existing(soup, ['[data-testid="industry-competencies"]', '.industry-competencies'])
            industry = self._parse_bullet_text(node, max_len=60)

        if not product:
            node = self._first_existing(soup, ['[data-testid="product-competencies"]', '.product-competencies'])
            product = self._parse_bullet_text(node, max_len=60)

        return {
            "industry_competencies": industry,
            "product_competencies": product,
        }

    # ============================================================
    # CONTACT & DOMAIN DISCOVERY
    # ============================================================

    def _parse_contact(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        publisher: dict[str, Any],
    ) -> dict[str, Any]:
        website = str(publisher.get("website") or "")

        # Fallback 1: learnMoreURL in consultant extension
        if not website:
            consultant_ext = listing.get("listing/extensions/consultant/listings/Listing", {})
            if isinstance(consultant_ext, dict) and consultant_ext.get("learnMoreURL"):
                website = str(consultant_ext.get("learnMoreURL"))

        # Fallback 2: extensions array learnMoreURL
        if not website:
            for ext in listing.get("extensions", []):
                if isinstance(ext, dict):
                    data = ext.get("data", {})
                    if isinstance(data, dict) and data.get("learnMoreURL"):
                        website = str(data.get("learnMoreURL"))
                        break

        # Fallback 3: LeadTrialInformation
        if not website:
            lead_info = listing.get("listing/plugins/LeadTrialInformation", {})
            if isinstance(lead_info, dict) and lead_info.get("learnMoreUrl"):
                website = str(lead_info.get("learnMoreUrl"))

        email = str(publisher.get("email") or "")
        phone = str(publisher.get("phone") or "")
        hq = str(publisher.get("hQLocation") or publisher.get("headquarters") or "")

        # Fallback 4: DOM parsing
        labels = soup.select(".appx-extended-detail-subsection-label")
        for label in labels:
            key = self._safe_text(label).lower()
            value = label.find_next_sibling("div")
            if value is None:
                continue
            text = self._safe_text(value)
            link = value.find("a")
            href = self._clean(link.get("href")) if link is not None else ""

            if "website" in key and not website:
                website = href or text
            elif "email" in key and not email:
                email = href.replace("mailto:", "") if href else text
            elif "phone" in key and not phone:
                phone = text
            elif "headquarters" in key and not hq:
                hq = text

        # Clean Domain Resolution
        domain = ""
        if website:
            clean_url = website if website.startswith(("http://", "https://")) else f"https://{website}"
            try:
                parsed = urlparse(clean_url)
                netloc = parsed.netloc.lower()
                if netloc.startswith("www."):
                    netloc = netloc[4:]
                if netloc and not any(s in netloc for s in ["salesforce.com", "appexchange.com"]):
                    domain = netloc
            except Exception:
                pass

        if not domain and email and "@" in email:
            mail_domain = email.split("@")[-1].lower().strip()
            if not any(s in mail_domain for s in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
                domain = mail_domain
                if not website:
                    website = f"https://www.{mail_domain}"

        return {
            "website": self._clean(website),
            "domain": self._clean(domain),
            "email": self._clean(email),
            "phone": self._clean(phone),
            "headquarters": self._clean(hq),
        }

    # ============================================================
    # ABOUT SECTION
    # ============================================================

    def _parse_about(
        self,
        soup: BeautifulSoup,
        publisher: dict[str, Any],
    ) -> dict[str, Any]:
        about: dict[str, Any] = {}
        if publisher.get("yearFounded"):
            about["Year Founded"] = str(publisher.get("yearFounded"))
        if publisher.get("employees"):
            about["Company Size"] = str(publisher.get("employees"))
        if publisher.get("hQLocation"):
            about["Headquarters"] = str(publisher.get("hQLocation"))
        if publisher.get("website"):
            about["Website"] = str(publisher.get("website"))

        labels = soup.select(".appx-extended-detail-subsection-label")
        for label in labels:
            key = self._safe_text(label)
            value = label.find_next_sibling("div")
            if value is None or key in about:
                continue
            link = value.find("a")
            if link is not None and link.get("href"):
                about[key] = self._clean(link.get("href"))
            else:
                about[key] = self._safe_text(value)

        return about

    # ============================================================
    # DESCRIPTION
    # ============================================================

    def _parse_description(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        publisher: dict[str, Any],
    ) -> list[str]:
        full_desc = str(
            listing.get("fullDescription")
            or listing.get("description")
            or publisher.get("description")
            or ""
        )
        if full_desc:
            paragraphs = [
                p.strip() for p in full_desc.split("\n") if len(p.strip()) > 20
            ]
            if paragraphs:
                return paragraphs
            return [full_desc]

        paragraphs: list[str] = []
        for item in soup.select(
            ".appx-multi-line-fixed, .appx-description, .slds-rich-text-editor__output p"
        ):
            text = self._safe_text(item)
            if text and len(text) > 40 and text not in paragraphs:
                paragraphs.append(text)

        return paragraphs

    # ============================================================
    # HIGHLIGHTS
    # ============================================================

    def _parse_highlights(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
    ) -> list[str]:
        comp = listing.get("consultantCompetencies", {})
        highlights = self._extract_names(comp.get("items") if isinstance(comp, dict) else [])

        if not highlights and listing.get("fullDescription"):
            lines = str(listing.get("fullDescription", "")).split("\n")
            for line in lines:
                line_s = line.strip()
                if line_s.startswith(("•", "★", "⦿", "-", "*")) and len(line_s) > 10:
                    highlights.append(line_s.lstrip("•★⦿-* "))

        if not highlights:
            for item in soup.select("li"):
                text = self._safe_text(item)
                if 15 < len(text) < 250:
                    highlights.append(text)

        return list(dict.fromkeys(highlights))[:15]

    # ============================================================
    # OVERVIEW
    # ============================================================

    def _parse_overview(
        self,
        soup: BeautifulSoup,
        listing: dict[str, Any],
        publisher: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "title": str(
                listing.get("seoTitle")
                or listing.get("name")
                or self._safe_text(soup.select_one(".appx-overview-title"))
                or ""
            ),
            "description": str(
                listing.get("fullDescription")
                or listing.get("description")
                or publisher.get("description")
                or self._safe_text(soup.select_one(".appx-multi-line-fixed"))
                or ""
            ),
        }
