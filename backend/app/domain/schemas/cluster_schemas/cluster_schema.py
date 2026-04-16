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
    avg_active_conditions: float


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


class ClusterSizeSchema(CamelModel):
    count: int
    percentage: float


class ClusterVitalsSchema(CamelModel):
    avg_age: float
    avg_bmi: float
    avg_systolic_bp: float
    avg_glucose: float
    avg_qaly: float
    avg_daly: float


class SeverityComponentsSchema(CamelModel):
    avg_active_conditions: float
    avg_medications: float
    avg_procedures: float


class ClusterUtilizationSchema(CamelModel):
    avg_active_conditions: float
    avg_medications: float
    avg_procedures: float
    avg_days_since_encounter: float
    avg_clinical_severity_score: float
    severity_components: SeverityComponentsSchema
    avg_routine_care: float
    avg_acute_care: float
    avg_wellness_care: float
    avg_severe_care: float
    avg_distinct_providers: float


class DiseasePrevalenceSchema(CamelModel):
    diabetes_pct: float
    hypertension_pct: float
    heart_disease_pct: float
    cancer_pct: float
    respiratory_pct: float
    mental_health_pct: float
    polypharmacy_pct: float


class DemographicsSchema(CamelModel):
    gender: Dict[str, float]
    marital: Dict[str, float]
    smoking: Dict[str, float]
    condition_burden: Dict[str, float]


class TopSequenceSchema(CamelModel):
    rank: int
    pattern_str: str
    length: int
    support_count: int
    support_pct: float
    cluster_support_count: int


class ClusterDetailResponse(CamelModel):
    cluster_id: int
    cluster_type: str
    title: str
    description: str
    insight: str
    recommendation: str
    color: str
    size: ClusterSizeSchema
    vitals: ClusterVitalsSchema
    utilization: ClusterUtilizationSchema
    disease_prevalence: DiseasePrevalenceSchema
    demographics: DemographicsSchema
    dominant_careplan: str
    dominant_encounter_class: str
    dominant_marital: str
    top_sequences: List[TopSequenceSchema]