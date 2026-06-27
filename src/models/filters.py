from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PartnerFilter:
    countries: list[str] = field(
        default_factory=lambda: ["United States of America"]
    )

    practice_size: list[str] = field(
        default_factory=lambda: ["1-5"]
    )

    expertises: list[str] = field(default_factory=list)

    specializations: list[str] = field(default_factory=list)

    states: list[str] = field(default_factory=list)

    rating: Optional[int] = None

    sorted_by: str = "expertise"

    offset: int = 0

    limit_size: int = 300

    from_finder: bool = False