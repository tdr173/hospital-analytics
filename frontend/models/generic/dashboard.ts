export type DashboardRange = "week" | "month" | "year" | "all";

export interface KpiCards {
  totalPatients: number;
  activePatients: number;
  totalProviders: number;
  totalOrganizations: number;
  totalEncounters: number;
  totalConditions: number;
  totalCareplans: number;
  totalProcedures: number;
  avgEncountersPerPatient: number;
  activeCareplans: number;
  newPatientsInPeriod: number;
  avgPatientAge: number;
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

export interface DailyEncounterItem {
  day: string;
  count: number;
}

export interface TopConditionItem {
  description: string;
  count: number;
}

export interface ClusterDistributionItem {
  title: string;
  count: number;
  color: string;
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
  topConditions: TopConditionItem[];
  clusterDistribution: ClusterDistributionItem[];
  genderDistribution: GenderDistributionItem[];
  ageGroups: AgeGroupItem[];
  encountersTimeline: DailyEncounterItem[];
  recentEncounters: RecentEncounterItem[];
}
