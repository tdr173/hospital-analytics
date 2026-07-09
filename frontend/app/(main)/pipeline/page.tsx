"use client";

import { useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import {
  getPipelineOverview,
  getPipelineStatus,
  startPipeline,
  stopPipeline,
} from "@/store/slices/pipeline/thunks";
import useClasses from "@/utils/useClasses";
import { PipelinePageStyles } from "./styles";
import PipelineRunCard from "./components/PipelineRunCard/PipelineRunCard";
import PipelineStatsGrid from "./components/PipelineStatsGrid/PipelineStatsGrid";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const POLL_INTERVAL_MS = 2000;

export default function PipelinePage() {
  const dispatch = useAppDispatch();
  const classes = useClasses(PipelinePageStyles, { name: "PipelinePage" });

  const { overview, loading, starting, stopping, error } = useSelector(
    (state: RootState) => state.pipeline,
  );

  const isRunning = overview?.status === "RUNNING";
  // track the previous running state so we can refetch stats once a run ends
  const wasRunning = useRef(false);

  useEffect(() => {
    dispatch(getPipelineOverview());
  }, [dispatch]);

  // Poll the lightweight status endpoint while a run is in progress. When the
  // run transitions out of RUNNING, refetch the full overview to refresh stats.
  useEffect(() => {
    if (!isRunning) {
      if (wasRunning.current) {
        wasRunning.current = false;
        dispatch(getPipelineOverview());
      }
      return;
    }
    wasRunning.current = true;
    const interval = setInterval(() => {
      dispatch(getPipelineStatus());
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [isRunning, dispatch]);

  const handleStart = () => {
    // startPipeline optimistically flips status to RUNNING on success, which
    // starts the poll loop below; the poll then tracks the real stage.
    dispatch(startPipeline());
  };

  const handleStop = () => {
    // stopPipeline just flags the run to halt at its next checkpoint; the
    // poll loop above picks up the eventual STOPPED status.
    dispatch(stopPipeline());
  };

  if (loading && !overview)
    return <div className={classes.loading}>Loading pipeline...</div>;
  if (error && !overview)
    return <div className={classes.error}>{error}</div>;
  if (!overview)
    return <div className={classes.empty}>No pipeline data available.</div>;

  return (
    <div className={classes.content}>
      <PipelineRunCard
        overview={overview}
        starting={starting}
        stopping={stopping}
        onStart={handleStart}
        onStop={handleStop}
      />
      <PipelineStatsGrid overview={overview} />
    </div>
  );
}
