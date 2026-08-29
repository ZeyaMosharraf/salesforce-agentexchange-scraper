"""
Search and Extraction Filter Configuration.

Configure which partners to extract by countries, practice size, expertises,
specializations, states, or rating.

Leave lists empty [] to scrape all records without filtering.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FilterConfig:
    """Partner search filter settings."""

    # Target countries (e.g. ["United States of America", "Canada", "United Kingdom"])
    # Leave empty [] for ALL countries
    countries: list[str] = field(default_factory=list)

    # Practice size tier (options: "1-5", "6-20", "21-50", "51-100", "100+")
    # Leave empty [] for ALL practice sizes
    practice_size: list[str] = field(default_factory=list)

    # Target expertises (e.g. ["Agentforce", "Sales Cloud", "Service Cloud"])
    expertises: list[str] = field(default_factory=list)

    # Target specializations (e.g. ["Financial Services", "Healthcare and Life Sciences"])
    specializations: list[str] = field(default_factory=list)

    # Target states / provinces (e.g. ["California", "New York", "Texas"])
    states: list[str] = field(default_factory=list)

    # Minimum AppExchange rating filter (e.g. 4, 5, or None for all)
    rating: Optional[int] = None

    # Sorting order (e.g. "expertise", "name", "rating")
    sorted_by: str = "expertise"

    # API batch size per request (default 500)
    limit_size: int = 500


# Active filter instance used by the extraction pipeline
filter_config = FilterConfig(
    countries=["United States of America"],
    practice_size=["1-5"],
    expertises=[],
    specializations=[],
    states=[],
    rating=None,
    sorted_by="expertise",
)
