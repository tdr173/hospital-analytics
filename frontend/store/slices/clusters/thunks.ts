import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import {
  ClustersResponse,
  PcaScatterResponse,
  NumericalFeaturesResponse,
  CategoricalFeaturesResponse,
  AiAnalysisResponse,
  ClusterDetailResponse,
} from "@/models/generic/clusters";
import { ErrorResponse } from "@/models/generic/generic";

import { apiUrl, API_BASE } from "@/utils/apiBases";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export { API_BASE };

export const getClusterStatistics = createAsyncThunk<
  PcaScatterResponse,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("getClusterStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(apiUrl(`/clusters/statistics`), {
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
}, {
  condition: (_, { getState }) => !getState().pcaScatter.loading,
});

export const getNumericalFeaturesStatistics = createAsyncThunk<
  NumericalFeaturesResponse,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("getNumericalFeaturesStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(apiUrl(`/clusters/numerical-features-statistics`), {
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
}, {
  condition: (_, { getState }) => !getState().numericalFeatures.loading,
});

export const getCategoricalFeaturesStatistics = createAsyncThunk<
  CategoricalFeaturesResponse,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("getCategoricalFeaturesStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(apiUrl(`/clusters/categorical-features-statistics`), {
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
}, {
  condition: (_, { getState }) => !getState().categoricalFeatures.loading,
});

export const getAiAnalysis = createAsyncThunk<
  AiAnalysisResponse,
  number,
  { state: RootState; rejectValue: ErrorResponse }
>("getAiAnalysis", async (clusterId, thunkAPI) => {
  try {
    const response = await fetch(apiUrl(`/clusters/ai-analysis/${clusterId}`), {
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
}, {
  condition: (clusterId, { getState }) => {
    const { cache, loading, currentClusterId } = getState().aiAnalysis;
    if (cache[clusterId]) return false;
    return !(loading && currentClusterId === clusterId);
  },
});

export const getClusterDetail = createAsyncThunk<
  ClusterDetailResponse,
  number,
  { state: RootState; rejectValue: ErrorResponse }
>("getClusterDetail", async (clusterId, thunkAPI) => {
  try {
    const response = await fetch(apiUrl(`/clusters/detail/${clusterId}`), {
      headers: defaultHeaders,
    });
    if (!response.ok) {
      toast.error("Failed to load cluster details", { toastId: "cluster-detail" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch cluster detail",
      });
    }
    return (await response.json()) as ClusterDetailResponse;
  } catch {
    toast.error("Failed to load cluster details", { toastId: "cluster-detail" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch cluster detail",
    });
  }
}, {
  condition: (_, { getState }) => !getState().clusterDetail.loading,
});

export const getClustersOverview = createAsyncThunk<
  ClustersResponse,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("getClustersOverview", async (_, thunkAPI) => {
  try {
    const response = await fetch(apiUrl(`/clusters`), {
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
}, {
  condition: (_, { getState }) => !getState().clusters.loading,
});
