export interface KpiCards {
  totalPatients: number;
  activePatients: number;
  totalProviders: number;
  totalOrganizations: number;
  totalEncounters: number;
}

export interface EncounterClassItem {
  encounterClass: string;
  count: number;
}

export interface GenderDistributionItem {
  gender: string;
  count: number;
}

export interface AgeGroupItem {
  ageGroup: string;
  count: number;
}

export interface MonthlyEncounterItem {
  month: string;
  count: number;
}

export interface RecentEncounterItem {
  encounterId: string;
  patientId: string;
  patientName: string;
  providerName: string;
  organizationName: string | null;
  startDate: string;
  encounterClass: string;
  description: string;
}

export interface DashboardData {
  kpis: KpiCards;
  encounterByClass: EncounterClassItem[];
  genderDistribution: GenderDistributionItem[];
  ageGroups: AgeGroupItem[];
  monthlyEncounters: MonthlyEncounterItem[];
  recentEncounters: RecentEncounterItem[];
}
