from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel


class FilterOption(BaseModel):
    value: str
    label: str


class PatientResourcesResponse(BaseModel):
    genders: List[FilterOption]
    age_groups: List[FilterOption]
    statuses: List[FilterOption]
    races: List[FilterOption]
    marital_statuses: List[FilterOption]


class PatientListItem(BaseModel):
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


class PatientListResponse(BaseModel):
    items: List[PatientListItem]
    total: int


class PatientDetailResponse(BaseModel):
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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cluster_label: Optional[int] = None
    cluster_title: Optional[str] = None
    cluster_color: Optional[str] = None


class PatientSummaryResponse(BaseModel):
    qaly: Optional[float] = None
    avg_bmi: Optional[float] = None
    active_conditions: Optional[int] = None
    total_medications: Optional[int] = None
    total_procedures: Optional[int] = None
    emergency_visits: Optional[int] = None
    days_since_last_encounter: Optional[int] = None


class ConditionItem(BaseModel):
    id: int
    description: str
    condition_code: str
    start_date: datetime
    end_date: Optional[datetime] = None


class MedicationItem(BaseModel):
    id: int
    description: str
    medication_code: str
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[float] = None
    reason_description: Optional[str] = None


class ProcedureItem(BaseModel):
    id: int
    description: str
    procedure_code: str
    date: datetime
    reason_description: Optional[str] = None


class ImmunizationItem(BaseModel):
    id: int
    description: str
    immunization_code: str
    date: datetime


class AllergyItem(BaseModel):
    id: int
    description: str
    allergy_code: str
    start_date: date
    end_date: Optional[date] = None


class EncounterItem(BaseModel):
    encounter_id: str
    start_date: datetime
    end_date: datetime
    duration: Optional[float] = None
    encounter_class: str
    description: str
    reason_description: Optional[str] = None
    provider_name: Optional[str] = None
    organization_name: Optional[str] = None
