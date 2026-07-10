from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PartnerFilter:

    countries: list[str] = field(
        default_factory=lambda: ["United States of America"]
    )

    practice_size: list[str] = field(
        default_factory=lambda: ["21-100"]
    )

    expertises: list[str] = field(
        default_factory=list
    )

    specializations: list[str] = field(
        default_factory=list
    )

    states: list[str] = field(
        default_factory=list
    )

    rating: Optional[int] = None

    sorted_by: str = "expertise"

    offset: int = 0

    limit_size: int = 300

    from_finder: bool = False

    def to_payload(self) -> dict:

            return {
                "namespace": "",
                "classname": "@udd/01p3m00000EBlzK",
                "method": "getPartners",
                "isContinuation": False,
                "params": {
                    "selectedFiltersFromJS": {
                        "expertises": self.expertises,
                        "specializations": self.specializations,
                        "countries": self.countries,
                        "states": self.states,
                        "rating": self.rating,
                        "practiceSize": self.practice_size,
                        "impactFilters": {},
                        "sortedBy": self.sorted_by,
                        "offset": self.offset,
                        "limitSize": self.limit_size,
                        "fromFinder": self.from_finder,
                    }
                },
                "cacheable": False,
            }