export interface PatientListItem {
  patient_id: string;
  first_name: string;
  last_name: string;
  age: number;
  gender: string | null;
  city: string | null;
  race: string | null;
  ethnicity: string | null;
  marital: string | null;
  birthdate: string | null;
  deathdate: string | null;
  cluster_label: number | null;
  cluster_title: string | null;
  cluster_color: string | null;
}

export interface PatientListResponse {
  items: PatientListItem[];
  total: number;
}

export interface PatientDetail {
  patient_id: string;
  first_name: string;
  last_name: string;
  age: number;
  gender: string | null;
  city: string | null;
  race: string | null;
  ethnicity: string | null;
  marital: string | null;
  birthdate: string | null;
  deathdate: string | null;
  latitude: number | null;
  longitude: number | null;
  cluster_label: number | null;
  cluster_title: string | null;
  cluster_color: string | null;
}

export interface PatientSummary {
  qaly: number | null;
  avg_bmi: number | null;
  active_conditions: number | null;
  total_medications: number | null;
  total_procedures: number | null;
  emergency_visits: number | null;
  days_since_last_encounter: number | null;
}

export interface ConditionItem {
  id: number;
  description: string;
  condition_code: string;
  start_date: string;
  end_date: string | null;
}

export interface MedicationItem {
  id: number;
  description: string;
  medication_code: string;
  start_date: string;
  end_date: string | null;
  duration_days: number | null;
  reason_description: string | null;
}

export interface ProcedureItem {
  id: number;
  description: string;
  procedure_code: string;
  date: string;
  reason_description: string | null;
}

export interface ImmunizationItem {
  id: number;
  description: string;
  immunization_code: string;
  date: string;
}

export interface AllergyItem {
  id: number;
  description: string;
  allergy_code: string;
  start_date: string;
  end_date: string | null;
}

export interface EncounterItem {
  encounter_id: string;
  start_date: string;
  end_date: string;
  duration: number | null;
  encounter_class: string;
  description: string;
  reason_description: string | null;
  provider_name: string | null;
  organization_name: string | null;
}

export interface FilterOption {
  value: string;
  label: string;
}

export interface PatientResources {
  genders: FilterOption[];
  age_groups: FilterOption[];
  statuses: FilterOption[];
  races: FilterOption[];
  marital_statuses: FilterOption[];
}

export interface FetchPatientsArgs {
  search?: string;
  gender?: string[];
  age_group?: string[];
  status?: string[];
  race?: string[];
  marital?: string[];
  city?: string;
  page: number;
  rows: number;
  sort_by: string;
  sort_type: string;
}
