import { createSlice } from "@reduxjs/toolkit";
import { ImmunizationStatisticsResponse } from "@/models/generic/statistics";
import { getImmunizationsStatistics } from "./thunks";

interface ImmunizationStatisticsState {
  data: ImmunizationStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ImmunizationStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const immunizationsStatisticsSlice = createSlice({
  name: "immunizationsStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getImmunizationsStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getImmunizationsStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getImmunizationsStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default immunizationsStatisticsSlice.reducer;
