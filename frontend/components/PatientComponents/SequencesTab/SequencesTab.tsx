"use client";

import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import IconButton from "@mui/material/IconButton";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { RootState, AppDispatch } from "@/store";
import { SequenceListItem } from "@/models/generic/sequences";
import {
  fetchSequenceResources,
  getSequenceAiAnalysis,
} from "@/store/slices/sequences/thunks";
import { openSequenceAnalysis } from "@/store/slices/sequences/sequence-ai-slice";
import useClasses from "@/utils/useClasses";
import sequencesTabStyles from "./SequencesTabStyles";
import SequenceCard from "@/app/(main)/sequences/components/SequenceCard/SequenceCard";
import SequenceAiModal from "@/app/(main)/sequences/components/SequenceAiModal/SequenceAiModal";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

interface Props {
  data: SequenceListItem[];
}

export default function SequencesTab({ data }: Props) {
  const classes = useClasses(sequencesTabStyles, { name: "SequencesTab" });
  const dispatch = useAppDispatch();
  const resources = useSelector((s: RootState) => s.sequenceResources.data);
  const aiCache = useSelector((s: RootState) => s.sequenceAi.cache);
  const [currentIdx, setCurrentIdx] = useState(0);

  useEffect(() => {
    if (!resources) {
      dispatch(fetchSequenceResources());
    }
  }, [dispatch, resources]);

  useEffect(() => {
    setCurrentIdx(0);
  }, [data]);

  const colors = resources?.colors ?? {};

  const handleAnalyse = (sequence: SequenceListItem) => {
    dispatch(openSequenceAnalysis(sequence));
    if (!aiCache[sequence.id]) {
      dispatch(getSequenceAiAnalysis(sequence.id));
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className={classes.emptyState}>
        No care sequences recorded for this patient.
      </div>
    );
  }

  const safeIdx = Math.min(currentIdx, data.length - 1);
  const current = data[safeIdx];
  const isFirst = safeIdx === 0;
  const isLast = safeIdx === data.length - 1;

  return (
    <div className={classes.container}>
      <div className={classes.list}>
        <SequenceCard
          key={current.id}
          sequence={current}
          colors={colors}
          onAnalyse={handleAnalyse}
        />
      </div>
      {data.length > 1 && (
        <div className={classes.paginationBar}>
          <IconButton
            size="small"
            disabled={isFirst}
            onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
            aria-label="Previous pattern"
            className={classes.navButton}
          >
            <ChevronLeftIcon />
          </IconButton>
          <span className={classes.position}>
            Sequence {safeIdx + 1} of {data.length}
          </span>
          <IconButton
            size="small"
            disabled={isLast}
            onClick={() =>
              setCurrentIdx((i) => Math.min(data.length - 1, i + 1))
            }
            aria-label="Next pattern"
            className={classes.navButton}
          >
            <ChevronRightIcon />
          </IconButton>
        </div>
      )}
      <SequenceAiModal colors={colors} />
    </div>
  );
}
