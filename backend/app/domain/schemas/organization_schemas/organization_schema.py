from typing import List, Optional
from datetime import datetime
from domain.schemas.camel_model import CamelModel
from domain.schemas.patient_schemas.patient_schema import FilterOption


class OrganizationResourcesResponse(CamelModel):
    cities: List[FilterOption]


class OrganizationListItem(CamelModel):
    organization_id: str
    name: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    utilization: int
    provider_count: int


class OrganizationListResponse(CamelModel):
    items: List[OrganizationListItem]
    total: int


class OrganizationDetailResponse(CamelModel):
    organization_id: str
    name: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float


class OrganizationProviderItem(CamelModel):
    provider_id: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    speciality: Optional[str] = None
    utilization: int


class OrganizationEncounterItem(CamelModel):
    encounter_id: str
    patient_id: str
    patient_name: str
    provider_id: str
    provider_name: str
    start_date: datetime
    end_date: datetime
    duration: Optional[float] = None
    encounter_class: str
    description: str
    reason_description: Optional[str] = None
