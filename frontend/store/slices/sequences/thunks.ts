import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import {
  SequenceListResponse,
  SequenceResourcesResponse,
  SequenceAiAnalysisResponse,
  FetchSequencesArgs,
} from "@/models/generic/sequences";
import { ErrorResponse } from "@/models/generic/generic";
import { API_BASE } from "@/store/slices/clusters/thunks";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export const fetchSequenceResources = createAsyncThunk<
  SequenceResourcesResponse,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("sequences/fetchResources", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/sequences/resources`, {
      headers: defaultHeaders,
    });
    if (!response.ok) {
      toast.error("Failed to load sequence resources", {
        toastId: "sequence-resources",
      });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch sequence resources",
      });
    }
    return (await response.json()) as SequenceResourcesResponse;
  } catch {
    toast.error("Failed to load sequence resources", {
      toastId: "sequence-resources",
    });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch sequence resources",
    });
  }
}, {
  condition: (_, { getState }) => {
    const s = getState().sequenceResources;
    return !s.loading && s.data === null;
  },
});

export const fetchSequences = createAsyncThunk<
  SequenceListResponse,
  FetchSequencesArgs,
  { state: RootState; rejectValue: ErrorResponse }
>("sequences/fetchList", async (args, thunkAPI) => {
  try {
    const q = new URLSearchParams();
    if (args.search) q.set("search", args.search);
    q.set("minLength", args.minLength.toString());
    q.set("sortBy", args.sortBy);
    q.set("sortType", args.sortType);
    q.set("page", args.page.toString());
    q.set("rows", args.rows.toString());
    const response = await fetch(`${API_BASE}/sequences?${q.toString()}`, {
      headers: defaultHeaders,
    });
    if (!response.ok) {
      toast.error("Failed to load sequences", { toastId: "sequences-list" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch sequences",
      });
    }
    return (await response.json()) as SequenceListResponse;
  } catch {
    toast.error("Failed to load sequences", { toastId: "sequences-list" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch sequences",
    });
  }
});

export const getSequenceAiAnalysis = createAsyncThunk<
  SequenceAiAnalysisResponse,
  number,
  { state: RootState; rejectValue: ErrorResponse }
>("sequences/getAiAnalysis", async (patternId, thunkAPI) => {
  try {
    const response = await fetch(
      `${API_BASE}/sequences/ai-analysis/${patternId}`,
      { headers: defaultHeaders },
    );
    if (!response.ok) {
      toast.error("Failed to generate AI analysis", {
        toastId: "sequence-ai-analysis",
      });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to generate AI analysis",
      });
    }
    return (await response.json()) as SequenceAiAnalysisResponse;
  } catch {
    toast.error("Failed to generate AI analysis", {
      toastId: "sequence-ai-analysis",
    });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to generate AI analysis",
    });
  }
}, {
  condition: (patternId, { getState }) => {
    const { cache, loading, currentPatternId } = getState().sequenceAi;
    if (cache[patternId]) return false;
    return !(loading && currentPatternId === patternId);
  },
});
