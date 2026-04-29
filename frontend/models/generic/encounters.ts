import { FilterOption } from "./patients";

export interface EncounterListItem {
  encounterId: string;
  patientId: string;
  patientName: string;
  providerName: string;
  organizationName: string | null;
  startDate: string;
  duration: number | null;
  encounterClass: string;
  description: string;
  reasonDescription: string | null;
}

export interface EncounterListResponse {
  items: EncounterListItem[];
  total: number;
}

export interface EncounterDetail {
  encounterId: string;
  patientId: string;
  patientName: string;
  providerId: string;
  providerName: string;
  organizationId: string;
  organizationName: string | null;
  startDate: string;
  endDate: string;
  duration: number | null;
  encounterClass: string;
  description: string;
  reasonDescription: string | null;
}

export interface EncounterObservationItem {
  id: number;
  date: string;
  observationCode: string;
  description: string;
  value: string;
  valueNumeric: number | null;
  units: string | null;
}

export interface EncounterConditionItem {
  id: number;
  conditionCode: string;
  description: string;
  startDate: string;
  endDate: string | null;
}

export interface EncounterMedicationItem {
  id: number;
  medicationCode: string;
  description: string;
  startDate: string;
  endDate: string | null;
  durationDays: number | null;
  reasonDescription: string | null;
}

export interface EncounterProcedureItem {
  id: number;
  procedureCode: string;
  description: string;
  startDate: string;
  endDate: string | null;
  reasonDescription: string | null;
}

export interface EncounterImmunizationItem {
  id: number;
  immunizationCode: string;
  description: string;
  date: string;
}

export interface EncounterAllergyItem {
  id: number;
  allergyCode: string;
  description: string;
  startDate: string;
  endDate: string | null;
}

export interface EncounterCarePlanItem {
  id: number;
  careplanCode: string;
  description: string;
  startDate: string;
  endDate: string | null;
  reasonDescription: string | null;
}

export interface EncounterResources {
  encounterClasses: FilterOption[];
}

export interface FetchEncountersArgs {
  search?: string;
  encounterClass?: string[];
  dateFrom?: string;
  dateTo?: string;
  page: number;
  rows: number;
  sortBy: string;
  sortType: "asc" | "desc";
}
