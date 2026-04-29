from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
from domain.schemas.camel_model import CamelModel


class FilterOption(CamelModel):
    value: str
    label: str


class PatientResourcesResponse(CamelModel):
    genders: List[FilterOption]
    age_groups: List[FilterOption]
    statuses: List[FilterOption]
    races: List[FilterOption]
    marital_statuses: List[FilterOption]


class PatientListItem(CamelModel):
    patient_id: str
    first_name: str
    last_name: str
    age: int
    gender: Optional[str] = None
    city: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    marital: Optional[str] = None
    birthdate: Optional[date] = None
    deathdate: Optional[date] = None
    cluster_label: Optional[int] = None
    cluster_title: Optional[str] = None
    cluster_color: Optional[str] = None


class PatientListResponse(CamelModel):
    items: List[PatientListItem]
    total: int


class PatientDetailResponse(CamelModel):
    patient_id: str
    first_name: str
    last_name: str
    age: int
    gender: Optional[str] = None
    city: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    marital: Optional[str] = None
    birthdate: Optional[date] = None
    deathdate: Optional[date] = None
    cluster_label: Optional[int] = None
    cluster_title: Optional[str] = None
    cluster_color: Optional[str] = None


class PatientSummaryResponse(CamelModel):
    qaly: Optional[float] = None
    avg_bmi: Optional[float] = None
    active_conditions: Optional[int] = None
    total_medications: Optional[int] = None
    total_procedures: Optional[int] = None
    emergency_visits: Optional[int] = None
    days_since_last_encounter: Optional[int] = None


class ConditionItem(CamelModel):
    id: int
    description: str
    condition_code: str
    start_date: datetime
    end_date: Optional[datetime] = None
    encounter_id: Optional[str] = None


class MedicationItem(CamelModel):
    id: int
    description: str
    medication_code: str
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[float] = None
    reason_description: Optional[str] = None
    encounter_id: Optional[str] = None


class ProcedureItem(CamelModel):
    id: int
    description: str
    procedure_code: str
    start_date: datetime
    end_date: Optional[datetime] = None
    reason_description: Optional[str] = None
    encounter_id: Optional[str] = None


class CarePlanItem(CamelModel):
    id: int
    description: str
    careplan_code: str
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[float] = None
    reason_description: Optional[str] = None
    encounter_id: Optional[str] = None


class ImmunizationItem(CamelModel):
    id: int
    description: str
    immunization_code: str
    date: datetime
    encounter_id: Optional[str] = None


class AllergyItem(CamelModel):
    id: int
    description: str
    allergy_code: str
    start_date: date
    end_date: Optional[date] = None
    encounter_id: Optional[str] = None


class PatientCreateRequest(CamelModel):
    first_name: str
    last_name: str
    age: int
    birthdate: Optional[date] = None
    deathdate: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    marital: Optional[str] = None
    city: Optional[str] = None


class PatientUpdateRequest(CamelModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    birthdate: Optional[date] = None
    deathdate: Optional[date] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    marital: Optional[str] = None
    city: Optional[str] = None


class PatientObservationItem(CamelModel):
    id: int
    date: datetime
    observation_code: str
    description: str
    value: str
    value_numeric: Optional[float] = None
    units: Optional[str] = None
    encounter_id: Optional[str] = None


class EncounterItem(CamelModel):
    encounter_id: str
    start_date: datetime
    end_date: datetime
    duration: Optional[float] = None
    encounter_class: str
    description: str
    reason_description: Optional[str] = None
    provider_name: Optional[str] = None
    organization_name: Optional[str] = None
