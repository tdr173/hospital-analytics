from typing import List, Optional
from datetime import datetime, date
from domain.schemas.camel_model import CamelModel
from domain.schemas.patient_schemas.patient_schema import FilterOption


class EncounterResourcesResponse(CamelModel):
    encounter_classes: List[FilterOption]


class EncounterListItem(CamelModel):
    encounter_id: str
    patient_id: str
    patient_name: str
    provider_name: str
    organization_name: Optional[str] = None
    start_date: datetime
    duration: Optional[float] = None
    encounter_class: str
    description: str
    reason_description: Optional[str] = None


class EncounterListResponse(CamelModel):
    items: List[EncounterListItem]
    total: int


class EncounterDetailResponse(CamelModel):
    encounter_id: str
    patient_id: str
    patient_name: str
    provider_id: str
    provider_name: str
    organization_id: str
    organization_name: Optional[str] = None
    start_date: datetime
    end_date: datetime
    duration: Optional[float] = None
    encounter_class: str
    description: str
    reason_description: Optional[str] = None


class EncounterObservationItem(CamelModel):
    id: int
    date: datetime
    observation_code: str
    description: str
    value: str
    value_numeric: Optional[float] = None
    units: Optional[str] = None


class EncounterConditionItem(CamelModel):
    id: int
    condition_code: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None


class EncounterMedicationItem(CamelModel):
    id: int
    medication_code: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[float] = None
    reason_description: Optional[str] = None


class EncounterProcedureItem(CamelModel):
    id: int
    procedure_code: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    reason_description: Optional[str] = None


class EncounterCarePlanItem(CamelModel):
    id: int
    careplan_code: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    reason_description: Optional[str] = None


class EncounterImmunizationItem(CamelModel):
    id: int
    immunization_code: str
    description: str
    date: datetime


class EncounterAllergyItem(CamelModel):
    id: int
    allergy_code: str
    description: str
    start_date: date
    end_date: Optional[date] = None
