"""QueryMetrics module for tracking query performance."""
from dataclasses import dataclass
from typing import List, Dict, Set


@dataclass
class QueryMetrics:
    """Track metrics for query performance."""
    query: str
    avg_score: float
    high_quality_count: int  # Number of results with score >= 4
    source_domains: set
    total_results: int

    @property
    def quality_ratio(self) -> float:
        """Calculate the ratio of high quality results to total results."""
        return self.high_quality_count / self.total_results if self.total_results > 0 else 0 