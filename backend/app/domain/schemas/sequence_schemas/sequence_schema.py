from typing import List, Dict
from domain.schemas.camel_model import CamelModel


class SequenceAiAnalysisResponse(CamelModel):
    clinical_interpretation: str
    layperson_summary: str
    risk_signals: List[str]
    recommendations: List[str]


class SequenceListItem(CamelModel):
    id: int
    rank: int
    pattern_str: str
    length: int
    support_count: int
    support_pct: float
    has_ai_analysis: bool


class SequenceListResponse(CamelModel):
    total: int
    items: List[SequenceListItem]


class SequenceSortOption(CamelModel):
    value: str
    label: str


class SequenceLengthRange(CamelModel):
    min_length: int
    max_length: int


class SequenceResourcesResponse(CamelModel):
    # Global scope length interval (cluster_label IS NULL).
    min_length: int
    max_length: int
    # Per-cluster length intervals, keyed by cluster_label (as string in JSON).
    cluster_ranges: Dict[int, SequenceLengthRange]
    colors: Dict[str, str]
    sort_options: List[SequenceSortOption]
