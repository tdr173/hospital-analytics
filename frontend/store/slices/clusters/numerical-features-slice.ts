import { createSlice } from "@reduxjs/toolkit";
import { NumericalFeaturesResponse } from "@/models/generic/clusters";
import { getNumericalFeaturesStatistics } from "./thunks";

interface NumericalFeaturesState {
  data: NumericalFeaturesResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: NumericalFeaturesState = {
  data: null,
  loading: true,
  error: null,
};

const numericalFeaturesSlice = createSlice({
  name: "numericalFeatures",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getNumericalFeaturesStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getNumericalFeaturesStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getNumericalFeaturesStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default numericalFeaturesSlice.reducer;
