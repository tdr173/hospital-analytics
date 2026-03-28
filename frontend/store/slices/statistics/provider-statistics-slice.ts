import { createSlice } from "@reduxjs/toolkit";
import { ProviderStatisticsResponse } from "@/models/generic/statistics";
import { getProvidersStatistics } from "./thunks";

interface ProviderStatisticsState {
  data: ProviderStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ProviderStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const providersStatisticsSlice = createSlice({
  name: "providersStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getProvidersStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getProvidersStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getProvidersStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default providersStatisticsSlice.reducer;
