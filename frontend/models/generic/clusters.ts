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
