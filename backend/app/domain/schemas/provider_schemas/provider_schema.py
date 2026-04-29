from typing import List, Optional
from datetime import datetime
from domain.schemas.camel_model import CamelModel
from domain.schemas.patient_schemas.patient_schema import FilterOption


class ProviderResourcesResponse(CamelModel):
    genders: List[FilterOption]
    specialities: List[FilterOption]


class ProviderListItem(CamelModel):
    provider_id: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    speciality: Optional[str] = None
    city: Optional[str] = None
    organization_name: Optional[str] = None
    encounters: int


class ProviderListResponse(CamelModel):
    items: List[ProviderListItem]
    total: int


class ProviderDetailResponse(CamelModel):
    provider_id: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    speciality: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    encounters: int
    organization_id: str
    organization_name: Optional[str] = None


class ProviderEncounterItem(CamelModel):
    encounter_id: str
    patient_id: str
    patient_name: str
    start_date: datetime
    end_date: datetime
    duration: Optional[float] = None
    encounter_class: str
    description: str
    reason_description: Optional[str] = None
