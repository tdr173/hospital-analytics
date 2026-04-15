export interface ChartEntry {
  name: string;
  value: number;
  tooltip: string;
}

export interface DurationStatsEntry {
  name: string;
  count: number;
  minDuration: number;
  maxDuration: number;
  avgDuration: number;
  medianDuration: number;
  tooltip: string;
}

export interface EncounterStatisticsResponse {
  totalEncounters: number;
  encounterClass: ChartEntry[];
  durationStats: DurationStatsEntry[];
  topDescriptions: ChartEntry[];
  topReasonDescriptions: ChartEntry[];
}

export interface PerPatientStats {
  avg: number;
  min: number;
  max: number;
}

export interface ConditionStatisticsResponse {
  totalConditions: number;
  uniqueConditions: number;
  perPatient: PerPatientStats;
  activeVsResolved: ChartEntry[];
  topConditions: ChartEntry[];
}

export interface NumericStatsEntry {
  name: string;
  count: number;
  patientCount: number;
  percentage: number;
  minValue: number;
  maxValue: number;
  avgValue: number;
  units: string;
  tooltip: string;
}

export interface CategoricalStatsEntry {
  name: string;
  count: number;
  patientCount: number;
  percentage: number;
  distinctValues: number;
  tooltip: string;
}

export interface ObservationStatisticsResponse {
  totalObservations: number;
  uniqueObservationTypes: number;
  perPatient: PerPatientStats;
  topObservationTypes: ChartEntry[];
  numericStats: NumericStatsEntry[];
  categoricalStats: CategoricalStatsEntry[];
}

export interface ProcedureStatisticsResponse {
  totalProcedures: number;
  uniqueProcedures: number;
  perPatient: PerPatientStats;
  topProcedures: ChartEntry[];
}

export interface ImmunizationStatisticsResponse {
  totalImmunizations: number;
  uniqueImmunizations: number;
  perPatient: PerPatientStats;
  topImmunizations: ChartEntry[];
}

export interface MedicationDurationStats {
  minDuration: number;
  maxDuration: number;
  avgDuration: number;
  medianDuration: number;
}

export interface UtilizationStats {
  min: number;
  max: number;
  avg: number;
  median: number;
}

export interface OrganizationStatisticsResponse {
  totalOrganizations: number;
  utilization: UtilizationStats;
  topCities: ChartEntry[];
}

export interface ProviderStatisticsResponse {
  totalProviders: number;
  uniqueSpecialities: number;
  utilization: UtilizationStats;
  gender: ChartEntry[];
  topSpecialities: ChartEntry[];
  topCities: ChartEntry[];
}

export interface AllergyStatisticsResponse {
  totalAllergies: number;
  uniqueAllergies: number;
  perPatient: PerPatientStats;
  activeVsResolved: ChartEntry[];
  topAllergies: ChartEntry[];
}

export interface MedicationStatisticsResponse {
  totalMedications: number;
  uniqueMedications: number;
  perPatient: PerPatientStats;
  durationStats: MedicationDurationStats;
  activeVsEnded: ChartEntry[];
  topMedications: ChartEntry[];
}

export interface CarePlanStatisticsResponse {
  totalCareplans: number;
  uniqueCareplans: number;
  perPatient: PerPatientStats;
  activeVsEnded: ChartEntry[];
  topCareplans: ChartEntry[];
}

export interface PatientStatisticsResponse {
  totalPatients: number;
  ageGroups: ChartEntry[];
  gender: ChartEntry[];
  race: ChartEntry[];
  ethnicity: ChartEntry[];
  maritalStatus: ChartEntry[];
  vitalStatus: ChartEntry[];
  topCities: ChartEntry[];
}
