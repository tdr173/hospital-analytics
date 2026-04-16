import { createSlice } from "@reduxjs/toolkit";
import { CategoricalFeaturesResponse } from "@/models/generic/clusters";
import { getCategoricalFeaturesStatistics } from "./thunks";

interface CategoricalFeaturesState {
  data: CategoricalFeaturesResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: CategoricalFeaturesState = {
  data: null,
  loading: false,
  error: null,
};

const categoricalFeaturesSlice = createSlice({
  name: "categoricalFeatures",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getCategoricalFeaturesStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getCategoricalFeaturesStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getCategoricalFeaturesStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default categoricalFeaturesSlice.reducer;
