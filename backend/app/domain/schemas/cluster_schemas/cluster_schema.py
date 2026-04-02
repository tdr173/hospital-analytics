from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field
from domain.schemas.camel_model import CamelModel


class ClusterDetails(CamelModel):
    model_config = ConfigDict(from_attributes=True)

    cluster_id: int = Field(validation_alias="cluster_label")
    color: str = "#006780"
    title: str
    description: str
    insight: str
    recommendation: str
    count: int
    percentage: float
    avg_age: float
    avg_qaly: float
    chronic_illness_pct: float
    avg_meds: float


class GetClustersDetails(CamelModel):
    total_patients: int
    clusters: List[ClusterDetails]


class PcaPoint(CamelModel):
    x: float
    y: float
    cluster: int
    is_outlier: bool


class GetClusterStatistics(CamelModel):
    points: List[PcaPoint]
    heatmap: Optional[str] = None  # base64-encoded PNG
    cluster_colors: Dict[int, str] = {}


class ChartEntry(CamelModel):
    name: str
    value: float
    tooltip: str


class FeatureChartData(CamelModel):
    feature: str
    data: List[ChartEntry]


class GetNumericalFeaturesStatistics(CamelModel):
    features: List[FeatureChartData]
    cluster_colors: Dict[int, str] = {}


class CategoricalClusterEntry(CamelModel):
    cluster_id: int
    proportions: Dict[str, float]


class CategoricalFeatureChartData(CamelModel):
    feature: str
    categories: List[str]
    data: List[CategoricalClusterEntry]


class GetCategoricalFeaturesStatistics(CamelModel):
    features: List[CategoricalFeatureChartData]
    cluster_colors: Dict[int, str] = {}


class AiAnalysisResponse(CamelModel):
    risk_level: str                          # "high" | "moderate" | "low"
    medical_interpretation: str
    layperson_summary: str
    key_characteristics: List[str]
    priority_interventions: List[str]
    care_recommendations: List[str]