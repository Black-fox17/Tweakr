from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResult:
    title: str
    authors: List[str]
    year: Optional[int]
    venue: Optional[str]
    url: Optional[str]
    citations: int
    source: str
    relevance_score: float = 0.0