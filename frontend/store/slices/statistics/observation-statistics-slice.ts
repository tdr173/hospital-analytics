import { createSlice } from "@reduxjs/toolkit";
import { ObservationStatisticsResponse } from "@/models/generic/statistics";
import { getObservationsStatistics } from "./thunks";

interface ObservationStatisticsState {
  data: ObservationStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ObservationStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const observationsStatisticsSlice = createSlice({
  name: "observationsStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getObservationsStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getObservationsStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getObservationsStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default observationsStatisticsSlice.reducer;
