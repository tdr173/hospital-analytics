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


class SequenceContinuationItem(SequenceListItem):
    matched_steps: int
    matched_pattern_str: str


class SequenceListResponse(CamelModel):
    total: int
    items: List[SequenceListItem]


class SequenceSortOption(CamelModel):
    value: str
    label: str


class SequenceResourcesResponse(CamelModel):
    min_length: int
    max_length: int
    colors: Dict[str, str]
    sort_options: List[SequenceSortOption]
