import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { SequenceAiAnalysisResponse } from "@/models/generic/sequences";
import { getSequenceAiAnalysis } from "./thunks";

interface SequenceAiState {
  cache: Record<number, SequenceAiAnalysisResponse>;
  currentPatternId: number | null;
  loading: boolean;
  error: string | null;
}

const initialState: SequenceAiState = {
  cache: {},
  currentPatternId: null,
  loading: false,
  error: null,
};

const sequenceAiSlice = createSlice({
  name: "sequenceAi",
  initialState,
  reducers: {
    openSequenceAnalysis: (state, action: PayloadAction<number>) => {
      state.currentPatternId = action.payload;
      state.error = null;
    },
    closeSequenceAnalysis: (state) => {
      state.currentPatternId = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getSequenceAiAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getSequenceAiAnalysis.fulfilled, (state, action) => {
        state.loading = false;
        if (state.currentPatternId !== null) {
          state.cache[state.currentPatternId] = action.payload;
        }
      })
      .addCase(getSequenceAiAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export const { openSequenceAnalysis, closeSequenceAnalysis } =
  sequenceAiSlice.actions;
export default sequenceAiSlice.reducer;
