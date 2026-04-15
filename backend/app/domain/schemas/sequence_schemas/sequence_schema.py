from typing import List, Optional
from domain.schemas.camel_model import CamelModel


class SequenceAiAnalysisResponse(CamelModel):
    clinical_interpretation: str
    layperson_summary: str
    risk_signals: List[str]
    recommendations: List[str]
