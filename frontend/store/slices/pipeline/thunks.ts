import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import { API_BASE } from "@/store/slices/clusters/thunks";
import { apiPost } from "@/store/slices/_apiClient";
import { ErrorResponse } from "@/models/generic/generic";
import { PipelineOverview, PipelineStatus } from "@/models/generic/pipeline";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export const getPipelineOverview = createAsyncThunk<
  PipelineOverview,
  void,
  { rejectValue: ErrorResponse }
>("pipeline/getOverview", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/pipeline`, { headers: defaultHeaders });
    if (!response.ok) {
      toast.error("Failed to load pipeline overview", { toastId: "pipeline-overview" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch pipeline overview",
      });
    }
    return (await response.json()) as PipelineOverview;
  } catch {
    toast.error("Failed to load pipeline overview", { toastId: "pipeline-overview" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch pipeline overview",
    });
  }
});

// Polling thunk - intentionally silent (no toast) so a transient poll failure
// doesn't spam the user while the pipeline runs.
export const getPipelineStatus = createAsyncThunk<
  PipelineStatus,
  void,
  { rejectValue: ErrorResponse }
>("pipeline/getStatus", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/pipeline/status`, { headers: defaultHeaders });
    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch pipeline status",
      });
    }
    return (await response.json()) as PipelineStatus;
  } catch {
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch pipeline status",
    });
  }
});

export const startPipeline = createAsyncThunk<
  PipelineStatus,
  void,
  { rejectValue: ErrorResponse }
>("pipeline/start", async (_, thunkAPI) => {
  try {
    // apiPost toasts on failure (e.g. 409 "Pipeline is already running")
    return await apiPost<PipelineStatus>(`${API_BASE}/pipeline/run`, {}, "start pipeline");
  } catch {
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to start pipeline",
    });
  }
});

export const stopPipeline = createAsyncThunk<
  PipelineStatus,
  void,
  { rejectValue: ErrorResponse }
>("pipeline/stop", async (_, thunkAPI) => {
  try {
    // apiPost toasts on failure (e.g. 409 "Pipeline is not running")
    return await apiPost<PipelineStatus>(`${API_BASE}/pipeline/stop`, {}, "stop pipeline");
  } catch {
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to stop pipeline",
    });
  }
});
