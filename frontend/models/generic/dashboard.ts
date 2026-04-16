export interface KpiCards {
  totalPatients: number;
  mortalityRate: number;
  totalProviders: number;
  totalOrganizations: number;
  totalEncounters: number;
  totalConditions: number;
  totalCareplans: number;
  totalProcedures: number;
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
  lastWeekEncounterByClass: EncounterClassItem[];
  topConditionsLastWeek: TopConditionItem[];
  clusterDistribution: ClusterDistributionItem[];
  genderDistribution: GenderDistributionItem[];
  ageGroups: AgeGroupItem[];
  lastMonthEncounters: DailyEncounterItem[];
  recentEncounters: RecentEncounterItem[];
}
