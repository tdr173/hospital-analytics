"use client";

import { CircularProgress } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import { PipelineOverview, PipelineStage } from "@/models/generic/pipeline";
import { PipelineRunCardStyles } from "./PipelineRunCardStyles";

interface Props {
  overview: PipelineOverview;
  starting: boolean;
  stopping: boolean;
  onStart: () => void;
  onStop: () => void;
}

const actionButtonSx = {
  display: "inline-flex",
  alignItems: "center",
  gap: "4px",
  height: "40px",
  padding: "6px",
  boxShadow: "none",
  border: "none",
  color: "#ffffff",
};

const STAGE_ORDER: PipelineStage[] = [
  "ETL",
  "CLUSTERING",
  "SEQUENCES_GLOBAL",
  "SEQUENCES_CLUSTERS",
  "DONE",
];

const STAGE_STEPS: { key: PipelineStage; label: string }[] = [
  { key: "ETL", label: "ETL" },
  { key: "CLUSTERING", label: "Clustering" },
  { key: "SEQUENCES_GLOBAL", label: "Sequences - Global" },
  { key: "SEQUENCES_CLUSTERS", label: "Sequences - Per-cluster" },
];

type StepState = "done" | "skipped" | "active" | "failed" | "stopped" | "pending";

const STATUS_COLORS: Record<string, string> = {
  IDLE: theme.colors.text.secondary,
  RUNNING: theme.colors.primary.main,
  SUCCESS: theme.colors.button.add,
  FAILED: theme.colors.status.error,
  STOPPED: theme.colors.status.warning,
};

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toLocaleString();
}

export default function PipelineRunCard({
  overview,
  starting,
  stopping,
  onStart,
  onStop,
}: Props) {
  const classes = useClasses(PipelineRunCardStyles, { name: "PipelineRunCard" });

  const { status, currentStage, etlSkipped, error } = overview;
  const isRunning = status === "RUNNING";
  const currentIdx = currentStage ? STAGE_ORDER.indexOf(currentStage) : -1;

  const stepState = (stageIdx: number): StepState => {
    if (status === "SUCCESS") {
      return stageIdx === 0 && etlSkipped ? "skipped" : "done";
    }
    if (status === "IDLE") return "pending";
    // RUNNING, FAILED, or STOPPED
    if (stageIdx < currentIdx) {
      return stageIdx === 0 && etlSkipped ? "skipped" : "done";
    }
    if (stageIdx === currentIdx) {
      if (status === "FAILED") return "failed";
      if (status === "STOPPED") return "stopped";
      return "active";
    }
    return "pending";
  };

  const renderStepIcon = (state: StepState) => {
    switch (state) {
      case "done":
      case "skipped":
        return (
          <CheckCircleIcon
            sx={{ color: theme.colors.button.add, fontSize: "1.25rem" }}
          />
        );
      case "active":
        return <CircularProgress size={18} sx={{ color: theme.colors.primary.main }} />;
      case "failed":
        return (
          <ErrorOutlineIcon
            sx={{ color: theme.colors.status.error, fontSize: "1.25rem" }}
          />
        );
      case "stopped":
        return (
          <StopIcon
            sx={{ color: theme.colors.status.warning, fontSize: "1.25rem" }}
          />
        );
      default:
        return (
          <RadioButtonUncheckedIcon
            sx={{ color: theme.colors.grey[300], fontSize: "1.25rem" }}
          />
        );
    }
  };

  const stepBadge = (state: StepState): string | null => {
    if (state === "skipped") return "Skipped";
    if (state === "done") return "Done";
    if (state === "active") return "Running";
    if (state === "failed") return "Failed";
    if (state === "stopped") return "Stopped";
    return null;
  };

  return (
    <div className={classes.card}>
      <div className={classes.header}>
        <div>
          <p className={classes.title}>Analytics Pipeline</p>
          <p className={classes.subtitle}>
            ETL -&gt; Clustering -&gt; Sequence mining
          </p>
        </div>
        <div className={classes.headerRight}>
          <span
            className={classes.statusBadge}
            style={{
              color: STATUS_COLORS[status] ?? theme.colors.text.secondary,
              borderColor: STATUS_COLORS[status] ?? theme.colors.text.secondary,
            }}
          >
            {isRunning && (
              <CircularProgress size={12} sx={{ color: "inherit", marginRight: "6px" }} />
            )}
            {status}
          </span>
          <StyledButton
            onClick={onStart}
            disabled={isRunning || starting}
            startIcon={<PlayArrowIcon />}
            sx={{
              ...actionButtonSx,
              background: theme.colors.button.add,
              "&:hover": {
                background: theme.colors.button.addHover,
                boxShadow: "none",
                transform: "none",
              },
              "&:active": {
                background: theme.colors.button.addActive,
                boxShadow: "none",
                transform: "none",
              },
            }}
          >
            Start
          </StyledButton>
          {isRunning && (
            <StyledButton
              onClick={onStop}
              disabled={stopping}
              startIcon={<StopIcon />}
              sx={{
                ...actionButtonSx,
                background: theme.colors.button.delete,
                "&:hover": {
                  background: theme.colors.button.deleteHover,
                  boxShadow: "none",
                  transform: "none",
                },
                "&:active": {
                  background: theme.colors.button.deleteActive,
                  boxShadow: "none",
                  transform: "none",
                },
              }}
            >
              Stop
            </StyledButton>
          )}
        </div>
      </div>

      <div className={classes.metaRow}>
        <div className={classes.metaItem}>
          <span className={classes.metaLabel}>Last run</span>
          <span className={classes.metaValue}>{formatDate(overview.lastRun)}</span>
        </div>
        <div className={classes.metaItem}>
          <span className={classes.metaLabel}>Next scheduled run</span>
          <span className={classes.metaValue}>{formatDate(overview.nextRun)}</span>
        </div>
        <div className={classes.metaItem}>
          <span className={classes.metaLabel}>Triggered by</span>
          <span className={classes.metaValue}>{overview.triggeredBy ?? "-"}</span>
        </div>
      </div>

      <div className={classes.stages}>
        {STAGE_STEPS.map((step, i) => {
          const state = stepState(i);
          const badge = stepBadge(state);
          return (
            <div key={step.key} className={classes.stage}>
              <div className={classes.stageIcon}>{renderStepIcon(state)}</div>
              <div className={classes.stageText}>
                <span className={classes.stageLabel}>{step.label}</span>
                {badge && (
                  <span
                    className={classes.stageBadge}
                    style={{
                      color:
                        state === "failed"
                          ? theme.colors.status.error
                          : state === "stopped"
                            ? theme.colors.status.warning
                            : state === "active"
                              ? theme.colors.primary.main
                              : theme.colors.text.secondary,
                    }}
                  >
                    {badge}
                  </span>
                )}
              </div>
              {i < STAGE_STEPS.length - 1 && <div className={classes.connector} />}
            </div>
          );
        })}
      </div>

      {status === "FAILED" && error && (
        <div className={classes.errorBox}>
          <ErrorOutlineIcon sx={{ fontSize: "1.1rem" }} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
