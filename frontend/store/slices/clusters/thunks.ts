import { createAsyncThunk } from "@reduxjs/toolkit";
import {
  ClustersResponse,
  PcaScatterResponse,
  NumericalFeaturesResponse,
  CategoricalFeaturesResponse,
  AiAnalysisResponse,
} from "@/models/generic/clusters";
import { ErrorResponse } from "@/models/generic/generic";

const API_BASE = "http://localhost:8000";

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
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch cluster statistics",
      });
    }

    return (await response.json()) as PcaScatterResponse;
  } catch {
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
      return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch numerical features" });
    }
    return (await response.json()) as NumericalFeaturesResponse;
  } catch {
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
      return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch categorical features" });
    }
    return (await response.json()) as CategoricalFeaturesResponse;
  } catch {
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
      return thunkAPI.rejectWithValue({ error: true, message: "Failed to generate AI analysis" });
    }
    return (await response.json()) as AiAnalysisResponse;
  } catch {
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
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch cluster data",
      });
    }

    return (await response.json()) as ClustersResponse;
  } catch {
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch cluster data",
    });
  }
});
