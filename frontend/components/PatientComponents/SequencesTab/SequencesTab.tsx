"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
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

  useEffect(() => {
    if (!resources) {
      dispatch(fetchSequenceResources());
    }
  }, [dispatch, resources]);

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

  return (
    <div className={classes.container}>
      <div className={classes.list}>
        {data.map((sequence) => (
          <SequenceCard
            key={sequence.id}
            sequence={sequence}
            colors={colors}
            onAnalyse={handleAnalyse}
          />
        ))}
      </div>
      <SequenceAiModal colors={colors} />
    </div>
  );
}
