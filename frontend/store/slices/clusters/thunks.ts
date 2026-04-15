import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import {
  ClustersResponse,
  PcaScatterResponse,
  NumericalFeaturesResponse,
  CategoricalFeaturesResponse,
  AiAnalysisResponse,
} from "@/models/generic/clusters";
import { ErrorResponse } from "@/models/generic/generic";

const API_BASE = "http://127.0.0.1:8000";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export { API_BASE };

export const getClusterStatistics = createAsyncThunk<
  PcaScatterResponse,
  void,
  { rejectValue: ErrorResponse }
>("getClusterStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/clusters/statistics`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load cluster statistics", { toastId: "cluster-statistics" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch cluster statistics",
      });
    }

    return (await response.json()) as PcaScatterResponse;
  } catch {
    toast.error("Failed to load cluster statistics", { toastId: "cluster-statistics" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch cluster statistics",
    });
  }
});

export const getNumericalFeaturesStatistics = createAsyncThunk<
  NumericalFeaturesResponse,
  void,
  { rejectValue: ErrorResponse }
>("getNumericalFeaturesStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/clusters/numerical-features-statistics`, {
      headers: defaultHeaders,
    });
    if (!response.ok) {
      toast.error("Failed to load numerical features", { toastId: "numerical-features" });
      return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch numerical features" });
    }
    return (await response.json()) as NumericalFeaturesResponse;
  } catch {
    toast.error("Failed to load numerical features", { toastId: "numerical-features" });
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch numerical features" });
  }
});

export const getCategoricalFeaturesStatistics = createAsyncThunk<
  CategoricalFeaturesResponse,
  void,
  { rejectValue: ErrorResponse }
>("getCategoricalFeaturesStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/clusters/categorical-features-statistics`, {
      headers: defaultHeaders,
    });
    if (!response.ok) {
      toast.error("Failed to load categorical features", { toastId: "categorical-features" });
      return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch categorical features" });
    }
    return (await response.json()) as CategoricalFeaturesResponse;
  } catch {
    toast.error("Failed to load categorical features", { toastId: "categorical-features" });
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch categorical features" });
  }
});

export const getAiAnalysis = createAsyncThunk<
  AiAnalysisResponse,
  number,
  { rejectValue: ErrorResponse }
>("getAiAnalysis", async (clusterId, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/clusters/ai-analysis/${clusterId}`, {
      headers: defaultHeaders,
    });
    if (!response.ok) {
      toast.error("Failed to generate AI analysis", { toastId: "ai-analysis" });
      return thunkAPI.rejectWithValue({ error: true, message: "Failed to generate AI analysis" });
    }
    return (await response.json()) as AiAnalysisResponse;
  } catch {
    toast.error("Failed to generate AI analysis", { toastId: "ai-analysis" });
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to generate AI analysis" });
  }
});

export const getClusterRuns = createAsyncThunk<
  ClustersResponse,
  void,
  { rejectValue: ErrorResponse }
>("getClusterRuns", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/clusters`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load cluster data", { toastId: "cluster-data" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch cluster data",
      });
    }

    return (await response.json()) as ClustersResponse;
  } catch {
    toast.error("Failed to load cluster data", { toastId: "cluster-data" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch cluster data",
    });
  }
});
