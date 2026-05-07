"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import CircularProgress from "@mui/material/CircularProgress";
import { useSelector } from "react-redux";
import { RootState } from "@/store";
import {
  PatientContinuationItem,
  SequenceListItem,
} from "@/models/generic/sequences";
import useClasses from "@/utils/useClasses";
import { PatternContinuationCardStyles } from "./PatternContinuationCardStyles";
import SequenceChipRowWithSplit from "@/app/(main)/sequences/components/SequenceChipRowWithSplit/SequenceChipRowWithSplit";

interface Props {
  continuation: PatientContinuationItem;
  colors: Record<string, string>;
  onAnalyse: (sequence: SequenceListItem) => void;
}

export default function PatternContinuationCard({
  continuation,
  colors,
  onAnalyse,
}: Props) {
  const classes = useClasses(PatternContinuationCardStyles, {
    name: "PatternContinuationCard",
  });
  const aiLoading = useSelector((s: RootState) => s.sequenceAi.loading);
  const aiCurrentId = useSelector((s: RootState) => s.sequenceAi.currentPatternId);
  const aiCached = useSelector(
    (s: RootState) => !!s.sequenceAi.cache[continuation.patternId],
  );

  const isThisLoading =
    aiLoading && aiCurrentId === continuation.patternId && !aiCached;

  const handleClick = () => {
    // Adapter: the AI modal accepts a SequenceListItem; construct one from
    // the continuation so the existing modal/cache pipeline can be reused.
    const adapted: SequenceListItem = {
      id: continuation.patternId,
      rank: continuation.rank,
      patternStr: continuation.patternStr,
      length: continuation.length,
      supportCount: continuation.supportCount,
      supportPct: continuation.supportPct,
      hasAiAnalysis: continuation.hasAiAnalysis,
    };
    onAnalyse(adapted);
  };

  return (
    <div className={classes.card}>
      <div className={classes.header}>
        <span className={classes.rankBadge}>#{continuation.rank}</span>
        <span className={classes.progressChip}>
          {continuation.prefixLength} of {continuation.length} steps already followed
        </span>
        {continuation.hasAiAnalysis && (
          <span className={classes.aiReadyBadge}>
            <span className={classes.aiReadyDot} />
            AI Insights Ready
          </span>
        )}
      </div>

      <SequenceChipRowWithSplit
        patternStr={continuation.patternStr}
        prefixLength={continuation.prefixLength}
        colors={colors}
      />

      <div className={classes.supportRow}>
        <span className={classes.supportLabel}>
          Followed by{" "}
          <span className={classes.supportValue}>
            {continuation.supportCount.toLocaleString()} patients
          </span>{" "}
          ({continuation.supportPct}%)
        </span>
        <button
          className={classes.analyseButton}
          onClick={handleClick}
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
