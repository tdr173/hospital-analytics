export interface SequenceListItem {
  id: number;
  rank: number;
  patternStr: string;
  length: number;
  supportCount: number;
  supportPct: number;
  hasAiAnalysis: boolean;
}

export interface SequenceListResponse {
  total: number;
  items: SequenceListItem[];
}

export interface SequenceSortOption {
  value: string;
  label: string;
}

export interface SequenceLengthRange {
  minLength: number;
  maxLength: number;
}

export interface SequenceResourcesResponse {
  // Global scope length interval.
  minLength: number;
  maxLength: number;
  // Per-cluster length intervals, keyed by cluster_label (string in JSON).
  clusterRanges: Record<string, SequenceLengthRange>;
  colors: Record<string, string>;
  sortOptions: SequenceSortOption[];
}

export interface SequenceAiAnalysisResponse {
  clinicalInterpretation: string;
  laypersonSummary: string;
  riskSignals: string[];
  recommendations: string[];
}

export interface FetchSequencesArgs {
  search?: string;
  minLength: number;
  sortBy: string;
  sortType: "asc" | "desc";
  page: number;
  rows: number;
  clusterLabels?: number[];
}
