from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field


class ClusterDetails(BaseModel):
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


class GetClustersDetails(BaseModel):
    total_patients: int
    clusters: List[ClusterDetails]


class PcaPoint(BaseModel):
    x: float
    y: float
    cluster: int
    is_outlier: bool


class GetClusterStatistics(BaseModel):
    points: List[PcaPoint]
    heatmap: Optional[str] = None  # base64-encoded PNG
    cluster_colors: Dict[int, str] = {}


class ChartEntry(BaseModel):
    name: str
    value: float
    tooltip: str


class FeatureChartData(BaseModel):
    feature: str
    data: List[ChartEntry]


class GetNumericalFeaturesStatistics(BaseModel):
    features: List[FeatureChartData]
    cluster_colors: Dict[int, str] = {}


class CategoricalClusterEntry(BaseModel):
    cluster_id: int
    proportions: Dict[str, float]


class CategoricalFeatureChartData(BaseModel):
    feature: str
    categories: List[str]
    data: List[CategoricalClusterEntry]


class GetCategoricalFeaturesStatistics(BaseModel):
    features: List[CategoricalFeatureChartData]
    cluster_colors: Dict[int, str] = {}


class AiAnalysisResponse(BaseModel):
    risk_level: str                          # "high" | "moderate" | "low"
    medical_interpretation: str
    layperson_summary: str
    key_characteristics: List[str]
    priority_interventions: List[str]
    care_recommendations: List[str]