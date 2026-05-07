"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import Select, { SelectChangeEvent } from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import { RootState, AppDispatch } from "@/store";
import {
  PatientContinuationItem,
  SequenceListItem,
} from "@/models/generic/sequences";
import { fetchPatientContinuations } from "@/store/slices/patients/thunks";
import { fetchSequenceResources } from "@/store/slices/sequences/thunks";
import { setContinuationsLastN } from "@/store/slices/patients/current-patient-slice";
import { openSequenceAnalysis } from "@/store/slices/sequences/sequence-ai-slice";
import { getSequenceAiAnalysis } from "@/store/slices/sequences/thunks";
import useClasses from "@/utils/useClasses";
import ContinuationsTabStyles from "./ContinuationsTabStyles";
import PatternContinuationCard from "./PatternContinuationCard";
import SequenceAiModal from "@/app/(main)/sequences/components/SequenceAiModal/SequenceAiModal";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

interface Props {
  patientId: string;
  data: PatientContinuationItem[];
}

const N_OPTIONS = [2, 3, 4, 5];

export default function ContinuationsTab({ patientId, data }: Props) {
  const classes = useClasses(ContinuationsTabStyles, { name: "ContinuationsTab" });
  const dispatch = useAppDispatch();
  const lastN = useSelector((s: RootState) => s.currentPatient.continuationsLastN);
  const resources = useSelector((s: RootState) => s.sequenceResources.data);
  const aiCache = useSelector((s: RootState) => s.sequenceAi.cache);

  useEffect(() => {
    if (!resources) {
      dispatch(fetchSequenceResources());
    }
  }, [dispatch, resources]);

  const colors = resources?.colors ?? {};

  const handleNChange = (e: SelectChangeEvent<number>) => {
    const newN = Number(e.target.value);
    if (newN === lastN) return;
    dispatch(setContinuationsLastN(newN));
    dispatch(fetchPatientContinuations({ patientId, lastN: newN, page: 1 }));
  };

  const handleAnalyse = (sequence: SequenceListItem) => {
    dispatch(openSequenceAnalysis(sequence));
    if (!aiCache[sequence.id]) {
      dispatch(getSequenceAiAnalysis(sequence.id));
    }
  };

  return (
    <div className={classes.container}>
      <div className={classes.toolbar}>
        <span className={classes.toolbarLabel}>Last N events used:</span>
        <Select
          value={lastN}
          onChange={handleNChange}
          size="small"
          className={classes.nSelect}
          aria-label="Number of recent events to anchor continuation matches"
        >
          {N_OPTIONS.map((n) => (
            <MenuItem key={n} value={n}>
              {n}
            </MenuItem>
          ))}
        </Select>
        <span className={classes.toolbarHint}>
          Patterns matching the last {lastN} clinical events
        </span>
      </div>

      {data.length === 0 ? (
        <div className={classes.emptyState}>
          No matching trajectories from the patient&apos;s last {lastN} events.
          Try increasing N or check after the next visit.
        </div>
      ) : (
        <div className={classes.list}>
          {data.map((c) => (
            <PatternContinuationCard
              key={c.patternId}
              continuation={c}
              colors={colors}
              onAnalyse={handleAnalyse}
            />
          ))}
        </div>
      )}

      <SequenceAiModal colors={colors} />
    </div>
  );
}
