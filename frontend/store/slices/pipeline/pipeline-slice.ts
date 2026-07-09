import { createSlice } from "@reduxjs/toolkit";
import { PipelineOverview, PipelineStatus } from "@/models/generic/pipeline";
import {
  getPipelineOverview,
  getPipelineStatus,
  startPipeline,
  stopPipeline,
} from "./thunks";

interface PipelineState {
  overview: PipelineOverview | null;
  status: PipelineStatus | null;
  loading: boolean;
  starting: boolean;
  stopping: boolean;
  error: string | null;
}

const initialState: PipelineState = {
  overview: null,
  status: null,
  loading: true,
  starting: false,
  stopping: false,
  error: null,
};

const pipelineSlice = createSlice({
  name: "pipeline",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getPipelineOverview.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getPipelineOverview.fulfilled, (state, action) => {
        state.loading = false;
        state.overview = action.payload;
        state.status = action.payload;
      })
      .addCase(getPipelineOverview.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      })
      .addCase(getPipelineStatus.fulfilled, (state, action) => {
        state.status = action.payload;
        // keep the run-card fields on the overview in sync during polling
        if (state.overview) {
          state.overview = { ...state.overview, ...action.payload };
        }
      })
      .addCase(startPipeline.pending, (state) => {
        state.starting = true;
      })
      .addCase(startPipeline.fulfilled, (state) => {
        state.starting = false;
        // The POST returns the pre-run snapshot (still IDLE); a 200 means the
        // run definitely started, so optimistically flip to RUNNING here so the
        // page's poll loop begins immediately. The first poll fills in the stage.
        const running = {
          status: "RUNNING" as const,
          currentStage: null,
          etlSkipped: false,
          triggeredBy: "manual",
          error: null,
          startedAt: new Date().toISOString(),
          finishedAt: null,
        };
        if (state.overview) {
          state.overview = { ...state.overview, ...running };
        }
        if (state.status) {
          state.status = { ...state.status, ...running };
        }
      })
      .addCase(startPipeline.rejected, (state) => {
        state.starting = false;
      })
      .addCase(stopPipeline.pending, (state) => {
        state.stopping = true;
      })
      .addCase(stopPipeline.fulfilled, (state, action) => {
        state.stopping = false;
        if (state.overview) state.overview = { ...state.overview, ...action.payload };
        if (state.status) state.status = { ...state.status, ...action.payload };
      })
      .addCase(stopPipeline.rejected, (state) => {
        state.stopping = false;
      });
  },
});

export default pipelineSlice.reducer;
