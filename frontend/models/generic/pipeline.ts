export type PipelineRunStatus =
  | "IDLE"
  | "RUNNING"
  | "SUCCESS"
  | "FAILED"
  | "STOPPED";

export type PipelineStage =
  | "ETL"
  | "CLUSTERING"
  | "SEQUENCES_GLOBAL"
  | "SEQUENCES_CLUSTERS"
  | "DONE";

export interface PipelineStatus {
  status: PipelineRunStatus;
  currentStage: PipelineStage | null;
  etlSkipped: boolean;
  triggeredBy: string | null;
  error: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  stopRequested: boolean;
}

export interface DataCounts {
  patients: number;
  medications: number;
  procedures: number;
  careplans: number;
  conditions: number;
}

export interface PipelineOverview extends PipelineStatus {
  lastRun: string | null;
  nextRun: string | null;
  interpretedClusters: number;
  totalClusters: number;
  interpretedSequences: number;
  totalSequences: number;
  counts: DataCounts;
}
