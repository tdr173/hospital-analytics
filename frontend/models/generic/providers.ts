import { FilterOption } from "./patients";

export interface ProviderListItem {
  providerId: string;
  firstName: string;
  lastName: string;
  gender: string | null;
  speciality: string | null;
  city: string | null;
  organizationName: string | null;
  encounters: number;
}

export interface ProviderListResponse {
  items: ProviderListItem[];
  total: number;
}

export interface ProviderDetail {
  providerId: string;
  firstName: string;
  lastName: string;
  gender: string | null;
  speciality: string | null;
  city: string | null;
  encounters: number;
  organizationId: string;
  organizationName: string | null;
}

export interface ProviderEncounterItem {
  encounterId: string;
  patientId: string;
  patientName: string;
  startDate: string;
  endDate: string;
  duration: number | null;
  encounterClass: string;
  description: string;
  reasonDescription: string | null;
}

export interface ProviderResources {
  genders: FilterOption[];
  specialities: FilterOption[];
}

export interface FetchProvidersArgs {
  search?: string;
  gender?: string[];
  speciality?: string[];
  city?: string;
  page: number;
  rows: number;
  sortBy: string;
  sortType: "asc" | "desc";
}
