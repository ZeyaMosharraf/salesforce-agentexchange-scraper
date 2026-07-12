import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from src.utils.logger import logger

class HtmlTransformation:

    def transform(self, html: str) -> dict[str, Any]:

        try:

                soup = BeautifulSoup(html, "lxml")

                result = {
                    "metadata": self._parse_metadata(soup),
                    "company": self._parse_company(soup),
                    "statistics": self._parse_statistics(soup),
                    "resources": self._parse_resources(soup),
                    "reviews": self._parse_reviews(soup),
                    "links": self._parse_links(soup),
                    "languages": self._parse_languages(soup),
                    "user_action": self._parse_user_actions(soup),
                    "geographic": self._parse_geographic_focus(soup),
                    "contact": self._parse_contact(soup),
                    "about": self._parse_about(soup),
                    "description" : self._parse_description(soup),
                    "highlight" : self._parse_highlights(soup),
                    "overview" : self._parse_overview(soup),
                }

                return result

        except Exception as e:

            logger.exception(
                "HTML transformation failed"
            )

            raise
    
    # ============================================================
    # HELPER FUNCTIONS
    # ============================================================

    def _clean(self, text: Optional[str]) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()


    def _safe_text(self, element) -> str:
        """Safely return cleaned text."""
        if element:
            return self._clean(element.get_text(" ", strip=True))
        return ""


    def _safe_attr(self,element, attr: str) -> str:
        """Safely return attribute."""
        if element and element.has_attr(attr):
            return self._clean(element[attr])
        return ""


    def _first_existing(self, soup, selectors: List[str]):
        """Return first matching selector."""
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                return node
        return None


    # ============================================================
    # METADATA
    # ============================================================

    def _parse_metadata(self, soup) -> Dict[str, Any]:

        logger.debug("Parsing metadata...")

        metadata = {}

        metadata["title"] = self._safe_text(
            soup.find("title")
        )

        metadata["canonical"] = self._safe_attr(
            soup.select_one("link[rel='canonical']"),
            "href"
        )

        metadata["description"] = self._safe_attr(
            soup.select_one("meta[name='description']"),
            "content"
        )

        metadata["keywords"] = self._safe_attr(
            soup.select_one("meta[name='keywords']"),
            "content"
        )

        metadata["robots"] = self._safe_attr(
            soup.select_one("meta[name='robots']"),
            "content"
        )

        metadata["language"] = self._safe_attr(
            soup.select_one("html"),
            "lang"
        )

        metadata["og"] = {}

        for meta in soup.select("meta[property^='og:']"):

            key = meta.get("property", "").replace("og:", "")

            metadata["og"][key] = self._clean(
                meta.get("content", "")
            )

        metadata["twitter"] = {}

        for meta in soup.select("meta[name^='twitter:']"):

            key = meta.get("name", "").replace("twitter:", "")

            metadata["twitter"][key] = self._clean(
                meta.get("content", "")
            )

        return metadata


    # ============================================================
    # COMPANY INFORMATION
    # ============================================================

    def _parse_company(self, soup) -> Dict[str, Any]:

        logger.debug("Parsing company information...")

        data = {}

        title = self._first_existing(
            soup,
            [
                "h1",
                ".appx-listing-title",
                ".listing-title",
                ".appx-title"
            ]
        )

        data["company_name"] = self._safe_text(title)

        logo = self._first_existing(
            soup,
            [
                ".appx-logo img",
                ".listing-logo img",
                ".partner-logo img",
                "img.appx-logo"
            ]
        )

        data["logo"] = self._safe_attr(
            logo,
            "src"
        )

        banner = self._first_existing(
            soup,
            [
                ".hero img",
                ".banner img",
                ".overview img"
            ]
        )

        data["banner"] = self._safe_attr(
            banner,
            "src"
        )

        data["tagline"] = ""

        overview = soup.select_one(
            ".appx-multi-line-fixed"
        )

        if overview:

            text = self._safe_text(
                overview
            )

            sentences = re.split(
                r"(?<=[.!?])\s+",
                text
            )

            if sentences:

                data["tagline"] = sentences[0]

        return data


    # ============================================================
    # STATISTICS
    # ============================================================

    def _parse_statistics(self, soup) -> Dict[str, Any]:

        logger.debug(
            "Parsing statistics..."
        )

        stats = {
            "rating": "",
            "review_count": "",
            "projects_completed": "",
            "certified_experts": "",
            "founded": "",
            "employees": ""
        }

        text = soup.get_text(
            " ",
            strip=True
        )

        rating = re.search(
            r"([0-5]\.\d+)",
            text
        )

        if rating:
            stats["rating"] = rating.group(1)

        review = re.search(
            r"(\d+)\s+Reviews?",
            text,
            re.I
        )

        if review:
            stats["review_count"] = review.group(1)

        project = re.search(
            r"(\d+)\s+Projects",
            text,
            re.I
        )

        if project:
            stats["projects_completed"] = project.group(1)

        expert = re.search(
            r"(\d+)\s+Certified",
            text,
            re.I
        )

        if expert:
            stats["certified_experts"] = expert.group(1)

        founded = re.search(
            r"Founded\s*(\d{4})",
            text,
            re.I
        )

        if founded:
            stats["founded"] = founded.group(1)

        return stats


    # ============================================================
    # OVERVIEW
    # ============================================================

    def _parse_overview(self, soup) -> Dict[str, Any]:

        logger.debug(
            "Parsing overview..."
        )

        overview = {}

        title = soup.select_one(
            ".appx-overview-title"
        )

        overview["title"] = self._safe_text(
            title
        )

        desc = soup.select_one(
            ".appx-multi-line-fixed"
        )

        overview["description"] = self._safe_text(
            desc
        )

        return overview


    # ============================================================
    # HIGHLIGHTS
    # ============================================================

    def _parse_highlights(self, soup) -> List[Dict[str, List[str]]]:

        logger.debug(
            "Parsing highlights..."
        )

        highlights = []

        for item in soup.select(
            "li"
        ):

            text = self._safe_text(item)

            if (
                len(text) > 15
                and len(text) < 250
            ):
                highlights.append(text)

        return list(dict.fromkeys(highlights))

    # ============================================================
    # DESCRIPTION
    # ============================================================

    def _parse_description(self, soup) -> List[str]:

        logger.debug(
            "Parsing description..."
        )

        paragraphs = []

        selectors = [

            ".appx-multi-line-fixed",

            ".appx-description",

            ".appx-description p",

            ".slds-rich-text-editor__output p",

            ".slds-rich-text-editor__output",

        ]

        visited = set()

        for selector in selectors:

            for item in soup.select(selector):

                text = self._safe_text(item)

                if (
                    text
                    and text not in visited
                    and len(text) > 40
                ):

                    visited.add(text)

                    paragraphs.append(text)

        return paragraphs


    # ============================================================
    # ABOUT SECTION
    # ============================================================

    def _parse_about(self, soup) -> Dict[str, Any]:

        logger.debug(
            "Parsing about section..."
        )

        about = {}

        labels = soup.select(
            ".appx-extended-detail-subsection-label"
        )

        for label in labels:

            key = self._safe_text(label)

            value = label.find_next_sibling(
                "div"
            )

            if not value:

                continue

            link = value.find("a")

            if link:

                href = link.get("href")

                if href:

                    about[key] = self._clean(href)

                else:

                    about[key] = self._safe_text(link)

            else:

                about[key] = self._safe_text(value)

        return about


    # ============================================================
    # CONTACT
    # ============================================================

    def _parse_contact(self, soup) -> Dict[str, Any]:

        logger.debug(
            "Parsing contact..."
        )

        contact = {

            "website": "",

            "email": "",

            "phone": "",

            "headquarters": "",

        }

        labels = soup.select(
            ".appx-extended-detail-subsection-label"
        )

        for label in labels:

            key = self._safe_text(label).lower()

            value = label.find_next_sibling(
                "div"
            )

            if not value:

                continue

            text = self._safe_text(value)

            href = ""

            link = value.find("a")

            if link:

                href = link.get(
                    "href",
                    ""
                )

            if "website" in key:

                contact["website"] = href or text

            elif "email" in key:

                contact["email"] = (
                    href.replace(
                        "mailto:",
                        ""
                    )
                    if href
                    else text
                )

            elif "phone" in key:

                contact["phone"] = text

            elif "headquarters" in key:

                contact["headquarters"] = text

        return contact


    # ============================================================
    # LANGUAGES
    # ============================================================

    def _parse_languages(self, soup) -> List[str]:

        logger.debug(
            "Parsing languages..."
        )

        languages = []

        for element in soup.find_all(
            string=re.compile(
                "Languages",
                re.I
            )
        ):

            parent = element.parent

            if not parent:

                continue

            block = parent.find_next()

            if not block:

                continue

            for item in block.find_all(
                [
                    "li",
                    "span",
                    "div"
                ]
            ):

                text = self._safe_text(item)

                if (
                    text
                    and len(text) < 40
                ):

                    languages.append(
                        text
                    )

        languages = list(
            dict.fromkeys(
                languages
            )
        )

        return languages


    # ============================================================
    # GEOGRAPHIC FOCUS
    # ============================================================

    def _parse_geographic_focus(self, soup) -> Dict[str, Any]:

        logger.debug(
            "Parsing geography..."
        )

        geo = {

            "countries": [],

            "states": [],

        }

        text = soup.get_text(
            " ",
            strip=True
        )

        country_patterns = [

            "United States",

            "Canada",

            "India",

            "Australia",

            "United Kingdom",

        ]

        for country in country_patterns:

            if country in text:

                geo[
                    "countries"
                ].append(
                    country
                )

        for div in soup.select(
            ".appx-country, .country"
        ):

            value = self._safe_text(div)

            if value:

                geo[
                    "countries"
                ].append(
                    value
                )

        for div in soup.select(
            ".appx-state, .state"
        ):

            value = self._safe_text(div)

            if value:

                geo[
                    "states"
                ].append(
                    value
                )

        geo["countries"] = list(
            dict.fromkeys(
                geo["countries"]
            )
        )

        geo["states"] = list(
            dict.fromkeys(
                geo["states"]
            )
        )

        return geo


    # ============================================================
    # RESOURCES
    # ============================================================

    def _parse_resources(self, soup) -> List[Dict[str, Any]]:

        logger.debug(
            "Parsing resources..."
        )

        resources = []

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = self._clean(
                link["href"]
            )

            title = self._safe_text(
                link
            )

            if not href:

                continue

            if any(
                x in href.lower()
                for x in [

                    ".pdf",

                    "resource",

                    "guide",

                    "ebook",

                    "datasheet",

                    "whitepaper",

                    "case",

                ]
            ):

                resources.append({

                    "title": title,

                    "url": href,

                })

        return  resources


    # ============================================================
    # REVIEWS
    # ============================================================

    def _parse_reviews(self, soup) -> List[Dict[str, Any]]:

        logger.debug(
            "Parsing reviews..."
        )

        reviews = []

        review_blocks = soup.select(
            ".review, .appx-review, .review-item"
        )

        for block in review_blocks:

            review = {

                "reviewer": "",

                "rating": "",

                "date": "",

                "review": "",

            }

            review["reviewer"] = self._safe_text(
                self._first_existing(
                    block,
                    [
                        ".reviewer",

                        ".author",

                        ".review-author",

                        ".name",
                    ]
                )
            )

            review["rating"] = self._safe_text(
                self._first_existing(
                    block,
                    [
                        ".rating",

                        ".stars",

                        ".review-rating",
                    ]
                )
            )

            review["date"] = self._safe_text(
                self._first_existing(
                    block,
                    [
                        ".date",

                        ".review-date",
                    ]
                )
            )

            review["review"] = self._safe_text(
                self._first_existing(
                    block,
                    [
                        ".content",

                        ".review-text",

                        ".review-body",
                    ]
                )
            )

            if any(review.values()):

                reviews.append(review)

        return reviews

    # ============================================================
    # APPX USER ACTIONS
    # ============================================================

    def _parse_user_actions(self, soup) -> Dict[str, Any]:

        logger.debug("Parsing AppxUserActions...")

        data = {
            "learn_more_url": ""
        }

        for script in soup.find_all("script"):

            script_text = script.get_text()

            if "learnMoreUrl" not in script_text:
                continue

            match = re.search(
                r"learnMoreUrl\s*:\s*['\"]([^'\"]+)['\"]",
                script_text
            )

            if match:
                data["learn_more_url"] = match.group(1)
                break

        return data

    # ============================================================
    # LINKS
    # ============================================================

    def _parse_links(self, soup) -> Dict[str, Any]:

        logger.debug(
            "Parsing links..."
        )

        links = {

            "internal": [],

            "external": [],

            "mailto": [],

            "telephone": [],

        }

        for a in soup.find_all(
            "a",
            href=True
        ):

            href = self._clean(
                a["href"]
            )

            if not href:

                continue

            if href.startswith(
                "mailto:"
            ):

                links[ "mailto"
                ].append( href.replace( "mailto:", "")
                )

            elif href.startswith(
                "tel:"
            ):

                links["telephone"
                ].append( href.replace( "tel:","")
                )

            elif href.startswith(
                "http"
            ):

                links["external"
                ].append(href)

            else:

                links["internal"
                ].append(href
                )

        for key in links:

            links[key] = list(
                dict.fromkeys(
                    links[key]
                )
            )

        return links

