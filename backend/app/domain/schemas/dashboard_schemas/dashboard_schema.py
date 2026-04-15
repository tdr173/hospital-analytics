from typing import List, Optional
from datetime import datetime
from domain.schemas.camel_model import CamelModel


class KpiCards(CamelModel):
    total_patients: int
    active_patients: int
    total_providers: int
    total_organizations: int
    total_encounters: int


class EncounterClassItem(CamelModel):
    encounter_class: str
    count: int


class GenderDistributionItem(CamelModel):
    gender: str
    count: int


class AgeGroupItem(CamelModel):
    age_group: str
    count: int


class MonthlyEncounterItem(CamelModel):
    month: str
    count: int


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
    encounter_by_class: List[EncounterClassItem]
    gender_distribution: List[GenderDistributionItem]
    age_groups: List[AgeGroupItem]
    monthly_encounters: List[MonthlyEncounterItem]
    recent_encounters: List[RecentEncounterItem]
