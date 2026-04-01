export interface ClusterSummary {
  cluster_id: number;
  color: string;
  title: string;
  description: string;
  insight: string;
  recommendation: string;
  count: number;
  percentage: number;
  avg_age: number;
  avg_qaly: number;
  chronic_illness_pct: number;
  avg_meds: number;
}

export interface ClustersResponse {
  total_patients: number;
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
  cluster_colors: Record<number, string>;
}

export interface CategoricalClusterEntry {
  cluster_id: number;
  proportions: Record<string, number>;
}

export interface CategoricalFeatureChartData {
  feature: string;
  categories: string[];
  data: CategoricalClusterEntry[];
}

export interface CategoricalFeaturesResponse {
  features: CategoricalFeatureChartData[];
  cluster_colors: Record<number, string>;
}

export interface PcaPoint {
  x: number;
  y: number;
  cluster: number;
  is_outlier: boolean;
}

export interface PcaScatterResponse {
  points: PcaPoint[];
  heatmap: string | null;
  cluster_colors: Record<number, string>;
}

export interface AiAnalysisResponse {
  risk_level: "high" | "moderate" | "low";
  medical_interpretation: string;
  layperson_summary: string;
  key_characteristics: string[];
  priority_interventions: string[];
  care_recommendations: string[];
}
