"use client";

import { useEffect, useMemo } from "react";
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

  const sequencesById = useMemo(() => {
    const map: Record<number, SequenceListItem> = {};
    for (const item of data) map[item.id] = item;
    return map;
  }, [data]);

  const handleAnalyse = (patternId: number) => {
    dispatch(openSequenceAnalysis(patternId));
    if (!aiCache[patternId]) {
      dispatch(getSequenceAiAnalysis(patternId));
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className={classes.emptyState}>
        No sequential patterns recorded for this patient.
      </div>
    );
  }

  return (
    <div className={classes.container}>
      <div className={classes.countBar}>
        {data.length} pattern{data.length === 1 ? "" : "s"} found for this patient
      </div>
      <div className={classes.list}>
        {data.map((seq) => (
          <SequenceCard
            key={seq.id}
            sequence={seq}
            colors={colors}
            onAnalyse={handleAnalyse}
          />
        ))}
      </div>
      <SequenceAiModal sequencesById={sequencesById} colors={colors} />
    </div>
  );
}
