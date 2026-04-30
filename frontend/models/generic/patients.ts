export interface PagedResponse<T> {
  items: T[];
  hasMore: boolean;
}

export interface PatientListItem {
  patientId: string;
  firstName: string;
  lastName: string;
  age: number;
  gender: string | null;
  city: string | null;
  race: string | null;
  ethnicity: string | null;
  marital: string | null;
  birthdate: string | null;
  deathdate: string | null;
  clusterLabel: number | null;
  clusterTitle: string | null;
  clusterColor: string | null;
}

export interface PatientListResponse {
  items: PatientListItem[];
  total: number;
}

export interface PatientDetail {
  patientId: string;
  firstName: string;
  lastName: string;
  age: number;
  gender: string | null;
  city: string | null;
  race: string | null;
  ethnicity: string | null;
  marital: string | null;
  birthdate: string | null;
  deathdate: string | null;
  clusterLabel: number | null;
  clusterTitle: string | null;
  clusterColor: string | null;
}

export interface PatientSummary {
  qaly: number | null;
  avgBmi: number | null;
  activeConditions: number | null;
  totalMedications: number | null;
  totalProcedures: number | null;
  emergencyVisits: number | null;
  daysSinceLastEncounter: number | null;
}

export interface ConditionItem {
  id: number;
  description: string;
  conditionCode: string;
  startDate: string;
  endDate: string | null;
  encounterId: string | null;
}

export interface MedicationItem {
  id: number;
  description: string;
  medicationCode: string;
  startDate: string;
  endDate: string | null;
  durationDays: number | null;
  reasonDescription: string | null;
  encounterId: string | null;
}

export interface ProcedureItem {
  id: number;
  description: string;
  procedureCode: string;
  startDate: string;
  endDate: string | null;
  reasonDescription: string | null;
  encounterId: string | null;
}

export interface ImmunizationItem {
  id: number;
  description: string;
  immunizationCode: string;
  date: string;
  encounterId: string | null;
}

export interface AllergyItem {
  id: number;
  description: string;
  allergyCode: string;
  startDate: string;
  endDate: string | null;
  encounterId: string | null;
}

export interface EncounterItem {
  encounterId: string;
  startDate: string;
  endDate: string;
  duration: number | null;
  encounterClass: string;
  description: string;
  reasonDescription: string | null;
  providerName: string | null;
  organizationName: string | null;
}

export interface CarePlanItem {
  id: number;
  description: string;
  careplanCode: string;
  startDate: string;
  endDate: string | null;
  durationDays: number | null;
  reasonDescription: string | null;
  encounterId: string | null;
}

export interface FilterOption {
  value: string;
  label: string;
}

export interface PatientResources {
  genders: FilterOption[];
  ageGroups: FilterOption[];
  statuses: FilterOption[];
  races: FilterOption[];
  maritalStatuses: FilterOption[];
}

export interface FetchPatientsArgs {
  search?: string;
  gender?: string[];
  ageGroup?: string[];
  status?: string[];
  race?: string[];
  marital?: string[];
  city?: string;
  page: number;
  rows: number;
  sortBy: string;
  sortType: string;
}
