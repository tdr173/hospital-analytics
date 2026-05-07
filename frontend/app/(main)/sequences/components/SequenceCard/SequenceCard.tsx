"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import CircularProgress from "@mui/material/CircularProgress";
import { useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { RootState } from "@/store";
import { SequenceListItem } from "@/models/generic/sequences";
import { SequenceCardStyles } from "./SequenceCardStyles";
import SequenceChipRow from "../SequenceChipRow/SequenceChipRow";

interface Props {
  sequence: SequenceListItem;
  colors: Record<string, string>;
  onAnalyse: (sequence: SequenceListItem) => void;
}

export default function SequenceCard({ sequence, colors, onAnalyse }: Props) {
  const classes = useClasses(SequenceCardStyles, { name: "SequenceCard" });
  const aiLoading = useSelector((s: RootState) => s.sequenceAi.loading);
  const aiCurrentId = useSelector((s: RootState) => s.sequenceAi.currentPatternId);
  const aiCached = useSelector(
    (s: RootState) => !!s.sequenceAi.cache[sequence.id],
  );
  const isThisLoading =
    aiLoading && aiCurrentId === sequence.id && !aiCached;

  const clampedPct = Math.max(0, Math.min(100, sequence.supportPct));

  return (
    <div className={classes.card}>
      <div className={classes.header}>
        <span className={classes.rankBadge}>#{sequence.rank}</span>
        {sequence.hasAiAnalysis && (
          <span className={classes.aiReadyBadge}>
            <span className={classes.aiReadyDot} />
            AI Insights Ready
          </span>
        )}
      </div>

      <SequenceChipRow patternStr={sequence.patternStr} colors={colors} />

      <div className={classes.supportBlock}>
        <div className={classes.supportRow}>
          <span className={classes.supportLabel}>
            Frequency: <span className={classes.supportValue}>{sequence.supportPct}%</span>
          </span>
          <span className={classes.supportValue}>
            {sequence.supportCount.toLocaleString()} patients
          </span>
        </div>
        <div className={classes.supportBarTrack}>
          <div
            className={classes.supportBarFill}
            style={{
              width: `${clampedPct}%`,
              backgroundColor: "#006780",
            }}
          />
        </div>
      </div>

      <div className={classes.footer}>
        <span className={classes.metaText}>
          Steps:{" "}
          <span className={classes.metaValue}>
            {sequence.length} {sequence.length === 1 ? "Step" : "Steps"}
          </span>
        </span>
        <button
          className={classes.analyseButton}
          onClick={() => onAnalyse(sequence)}
          type="button"
          disabled={isThisLoading}
          aria-label="Get AI insights for this pattern"
        >
          {isThisLoading ? (
            <CircularProgress size={14} sx={{ color: "#fff" }} />
          ) : (
            <AutoAwesomeIcon style={{ fontSize: 15 }} />
          )}
          Get AI Insights
        </button>
      </div>
    </div>
  );
}
