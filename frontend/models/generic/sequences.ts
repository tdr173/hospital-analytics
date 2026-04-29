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

export interface SequenceResourcesResponse {
  minLength: number;
  maxLength: number;
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
}
