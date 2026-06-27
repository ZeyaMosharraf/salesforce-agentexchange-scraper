from dataclasses import dataclass

@dataclass(slots=True)
class Partner:
    company_name: str
    website: str
    country: str
    state: str
    rating: float | None
    practice_size: str