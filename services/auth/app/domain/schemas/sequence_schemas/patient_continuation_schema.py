from domain.schemas.camel_model import CamelModel


class PatientContinuationItem(CamelModel):
    pattern_id: int
    rank: int
    pattern_str: str
    length: int
    support_count: int
    support_pct: float
    has_ai_analysis: bool
    prefix_length: int
    continuation_length: int
    matched_prefix_str: str
