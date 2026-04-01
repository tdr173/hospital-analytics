import { createSlice } from "@reduxjs/toolkit";
import { AiAnalysisResponse } from "@/models/generic/clusters";
import { getAiAnalysis } from "./thunks";

interface AiAnalysisState {
  cache: Record<number, AiAnalysisResponse>;   // cluster_id → cached result
  currentClusterId: number | null;
  loading: boolean;
  error: string | null;
}

const initialState: AiAnalysisState = {
  cache: {},
  currentClusterId: null,
  loading: false,
  error: null,
};

const aiAnalysisSlice = createSlice({
  name: "aiAnalysis",
  initialState,
  reducers: {
    openAnalysis: (state, action: { payload: number }) => {
      state.currentClusterId = action.payload;
      state.error = null;
    },
    closeAnalysis: (state) => {
      state.currentClusterId = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getAiAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getAiAnalysis.fulfilled, (state, action) => {
        state.loading = false;
        if (state.currentClusterId !== null) {
          state.cache[state.currentClusterId] = action.payload;
        }
      })
      .addCase(getAiAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export const { openAnalysis, closeAnalysis } = aiAnalysisSlice.actions;
export default aiAnalysisSlice.reducer;
