export interface ClusterSummary {
  clusterId: number;
  color: string;
  title: string;
  description: string;
  insight: string;
  recommendation: string;
  count: number;
  percentage: number;
  avgAge: number;
  avgQaly: number;
  chronicIllnessPct: number;
  avgMeds: number;
  avgActiveConditions: number;
}

export interface ClustersResponse {
  totalPatients: number;
  clusters: ClusterSummary[];
}

export interface ClusterChartEntry {
  name: string;
  value: number;
  tooltip: string;
}

export interface FeatureChartData {
  feature: string;
  data: ClusterChartEntry[];
}

export interface NumericalFeaturesResponse {
  features: FeatureChartData[];
  clusterColors: Record<number, string>;
}

export interface CategoricalClusterEntry {
  clusterId: number;
  proportions: Record<string, number>;
}

export interface CategoricalFeatureChartData {
  feature: string;
  categories: string[];
  data: CategoricalClusterEntry[];
  height: number | null;
}

export interface CategoricalFeaturesResponse {
  features: CategoricalFeatureChartData[];
  clusterColors: Record<number, string>;
}

export interface PcaPoint {
  x: number;
  y: number;
  cluster: number;
  isOutlier: boolean;
}

export interface PcaScatterResponse {
  points: PcaPoint[];
  heatmap: string | null;
  pcaImage: string | null;
  clusterColors: Record<number, string>;
}

export interface AiAnalysisResponse {
  riskLevel: "high" | "moderate" | "low";
  medicalInterpretation: string;
  laypersonSummary: string;
  keyCharacteristics: string[];
  priorityInterventions: string[];
  careRecommendations: string[];
}

export interface ClusterSize {
  count: number;
  percentage: number;
}

export interface ClusterVitals {
  avgAge: number;
  avgBmi: number;
  avgSystolicBp: number;
  avgGlucose: number;
  avgQaly: number;
  avgDaly: number;
}

export interface SeverityComponents {
  avgActiveConditions: number;
  avgMedications: number;
  avgProcedures: number;
}

export interface ClusterUtilization {
  avgActiveConditions: number;
  avgMedications: number;
  avgProcedures: number;
  avgDaysSinceEncounter: number;
  avgClinicalSeverityScore: number;
  severityComponents: SeverityComponents;
  avgRoutineCare: number;
  avgAcuteCare: number;
  avgWellnessCare: number;
  avgSevereCare: number;
  avgDistinctProviders: number;
}

export interface DiseasePrevalence {
  diabetesPct: number;
  hypertensionPct: number;
  heartDiseasePct: number;
  cancerPct: number;
  respiratoryPct: number;
  mentalHealthPct: number;
  polypharmacyPct: number;
}

export interface ClusterDemographics {
  gender: Record<string, number>;
  marital: Record<string, number>;
  smoking: Record<string, number>;
  conditionBurden: Record<string, number>;
}

export interface TopSequence {
  rank: number;
  patternStr: string;
  length: number;
  supportCount: number;
  supportPct: number;
  clusterSupportCount: number;
}

export interface ClusterDetailResponse {
  clusterId: number;
  clusterType: string;
  title: string;
  description: string;
  insight: string;
  recommendation: string;
  color: string;
  size: ClusterSize;
  vitals: ClusterVitals;
  utilization: ClusterUtilization;
  diseasePrevalence: DiseasePrevalence;
  demographics: ClusterDemographics;
  dominantCareplan: string;
  dominantEncounterClass: string;
  dominantMarital: string;
  topSequences: TopSequence[];
}
