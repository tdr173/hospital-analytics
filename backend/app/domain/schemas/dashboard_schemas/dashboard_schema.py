from typing import List, Optional
from datetime import datetime
from domain.schemas.camel_model import CamelModel


class KpiCards(CamelModel):
    total_patients: int
    mortality_rate: float
    total_providers: int
    total_organizations: int
    total_encounters: int
    total_conditions: int
    total_careplans: int
    total_procedures: int
    avg_encounters_per_patient: float
    active_careplans: int
    new_patients_last_30_days: int
    avg_patient_age: float


class EncounterClassItem(CamelModel):
    encounter_class: str
    count: int


class GenderDistributionItem(CamelModel):
    gender: str
    count: int


class AgeGroupItem(CamelModel):
    age_group: str
    count: int


class DailyEncounterItem(CamelModel):
    day: str
    count: int


class TopConditionItem(CamelModel):
    description: str
    count: int


class ClusterDistributionItem(CamelModel):
    title: str
    count: int
    color: str


class RecentEncounterItem(CamelModel):
    encounter_id: str
    patient_id: str
    patient_name: str
    provider_name: str
    organization_name: Optional[str] = None
    start_date: datetime
    encounter_class: str
    description: str


class DashboardResponse(CamelModel):
    kpis: KpiCards
    last_week_encounter_by_class: List[EncounterClassItem]
    top_conditions_last_week: List[TopConditionItem]
    cluster_distribution: List[ClusterDistributionItem]
    gender_distribution: List[GenderDistributionItem]
    age_groups: List[AgeGroupItem]
    last_month_encounters: List[DailyEncounterItem]
    recent_encounters: List[RecentEncounterItem]
