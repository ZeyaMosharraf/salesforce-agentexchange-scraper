"""
Search and Extraction Filter Configuration.

Configure which partners to extract by countries, practice size, expertises,
specializations, states, rating, or listing type.

Official Salesforce Practice Size Options:
["1-5", "6-20", "21-100", "101-200", "201-1000", "> 1000"]

Leave lists empty [] or rating=None to scrape all records without filtering.
"""

from dataclasses import dataclass, field
from typing import Optional

# Official Salesforce Practice Size options for reference
PRACTICE_SIZE_OPTIONS: list[str] = [
    "1-5",
    "6-20",
    "21-100",
    "101-200",
    "201-1000",
    "> 1000",
]

# Country name to ISO 2-letter location code lookup mapping
COUNTRY_TO_LOCATION_CODE: dict[str, str] = {
    "United States of America": "US",
    "United States": "US",
    "USA": "US",
    "Canada": "CA",
    "United Kingdom": "GB",
    "UK": "GB",
    "Australia": "AU",
    "Germany": "DE",
    "France": "FR",
    "India": "IN",
    "Japan": "JP",
    "Netherlands": "NL",
}


@dataclass
class FilterConfig:
    """Partner search and extraction filter settings."""

    # Target countries (e.g. ["United States of America", "Canada"])
    # Leave empty [] to extract ALL countries globally without geographic restriction
    countries: list[str] = field(default_factory=list)

    # Target practice sizes (e.g. ["1-5", "21-100"])
    # Leave empty [] for ALL practice sizes
    practice_size: list[str] = field(default_factory=list)

    # Target expertises (e.g. ["Agentforce", "Sales Cloud", "Service Cloud"])
    # Leave empty [] for ALL expertises
    expertises: list[str] = field(default_factory=list)

    # Target specializations (e.g. ["Financial Services", "Healthcare and Life Sciences"])
    # Leave empty [] for ALL specializations
    specializations: list[str] = field(default_factory=list)

    # Target states / provinces (e.g. ["California", "New York", "Texas"])
    # Leave empty [] for ALL states
    states: list[str] = field(default_factory=list)

    # Minimum AppExchange rating filter (e.g. 4.0, 4.5, or None for ALL)
    rating: Optional[float] = None

    # Listing type filter ("consultants" for consulting partners, "apps" for ISV products)
    listing_type: str = "consultants"

    # API batch size per request (max 100)
    page_size: int = 100


# Active filter instance used by the extraction pipeline
filter_config = FilterConfig(
    countries=[],
    practice_size=[],
    expertises=[],
    specializations=[],
    states=[],
    rating=None,
    listing_type="consultants",
    page_size=100,
)
