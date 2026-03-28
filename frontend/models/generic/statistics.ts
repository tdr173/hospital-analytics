export interface ChartEntry {
  name: string;
  value: number;
  tooltip: string;
}

export interface DurationStatsEntry {
  name: string;
  count: number;
  min_duration: number;
  max_duration: number;
  avg_duration: number;
  median_duration: number;
  tooltip: string;
}

export interface EncounterStatisticsResponse {
  total_encounters: number;
  encounter_class: ChartEntry[];
  duration_stats: DurationStatsEntry[];
  top_descriptions: ChartEntry[];
  top_reason_descriptions: ChartEntry[];
}

export interface PerPatientStats {
  avg: number;
  min: number;
  max: number;
}

export interface ConditionStatisticsResponse {
  total_conditions: number;
  unique_conditions: number;
  per_patient: PerPatientStats;
  active_vs_resolved: ChartEntry[];
  top_conditions: ChartEntry[];
}

export interface NumericStatsEntry {
  name: string;
  count: number;
  patient_count: number;
  percentage: number;
  min_value: number;
  max_value: number;
  avg_value: number;
  units: string;
  tooltip: string;
}

export interface CategoricalStatsEntry {
  name: string;
  count: number;
  patient_count: number;
  percentage: number;
  distinct_values: number;
  tooltip: string;
}

export interface ObservationStatisticsResponse {
  total_observations: number;
  unique_observation_types: number;
  per_patient: PerPatientStats;
  top_observation_types: ChartEntry[];
  numeric_stats: NumericStatsEntry[];
  categorical_stats: CategoricalStatsEntry[];
}

export interface ProcedureStatisticsResponse {
  total_procedures: number;
  unique_procedures: number;
  per_patient: PerPatientStats;
  top_procedures: ChartEntry[];
}

export interface ImmunizationStatisticsResponse {
  total_immunizations: number;
  unique_immunizations: number;
  per_patient: PerPatientStats;
  top_immunizations: ChartEntry[];
}

export interface MedicationDurationStats {
  min_duration: number;
  max_duration: number;
  avg_duration: number;
  median_duration: number;
}

export interface UtilizationStats {
  min: number;
  max: number;
  avg: number;
  median: number;
}

export interface OrganizationStatisticsResponse {
  total_organizations: number;
  utilization: UtilizationStats;
  top_cities: ChartEntry[];
}

export interface ProviderStatisticsResponse {
  total_providers: number;
  unique_specialities: number;
  utilization: UtilizationStats;
  gender: ChartEntry[];
  top_specialities: ChartEntry[];
  top_cities: ChartEntry[];
}

export interface AllergyStatisticsResponse {
  total_allergies: number;
  unique_allergies: number;
  per_patient: PerPatientStats;
  active_vs_resolved: ChartEntry[];
  top_allergies: ChartEntry[];
}

export interface MedicationStatisticsResponse {
  total_medications: number;
  unique_medications: number;
  per_patient: PerPatientStats;
  duration_stats: MedicationDurationStats;
  active_vs_ended: ChartEntry[];
  top_medications: ChartEntry[];
}

export interface PatientStatisticsResponse {
  total_patients: number;
  age_groups: ChartEntry[];
  gender: ChartEntry[];
  race: ChartEntry[];
  ethnicity: ChartEntry[];
  marital_status: ChartEntry[];
  vital_status: ChartEntry[];
  top_cities: ChartEntry[];
}
