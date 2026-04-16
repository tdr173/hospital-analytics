import { FilterOption } from "./patients";

export interface OrganizationListItem {
  organizationId: string;
  name: string | null;
  city: string | null;
  phone: string | null;
  utilization: number;
  providerCount: number;
}

export interface OrganizationListResponse {
  items: OrganizationListItem[];
  total: number;
}

export interface OrganizationDetail {
  organizationId: string;
  name: string | null;
  city: string | null;
  latitude: number;
  longitude: number;
}

export interface OrganizationProviderItem {
  providerId: string;
  firstName: string;
  lastName: string;
  gender: string | null;
  speciality: string | null;
  utilization: number;
}

export interface OrganizationEncounterItem {
  encounterId: string;
  patientId: string;
  patientName: string;
  providerId: string;
  providerName: string;
  startDate: string;
  endDate: string;
  duration: number | null;
  encounterClass: string;
  description: string;
  reasonDescription: string | null;
}

export interface OrganizationResources {
  cities: FilterOption[];
}

export interface FetchOrganizationsArgs {
  search?: string;
  city?: string;
  page: number;
  rows: number;
  sortBy: string;
  sortType: "asc" | "desc";
}
