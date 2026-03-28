import { createSlice } from "@reduxjs/toolkit";
import { MedicationStatisticsResponse } from "@/models/generic/statistics";
import { getMedicationsStatistics } from "./thunks";

interface MedicationStatisticsState {
  data: MedicationStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: MedicationStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const medicationsStatisticsSlice = createSlice({
  name: "medicationsStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getMedicationsStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getMedicationsStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getMedicationsStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default medicationsStatisticsSlice.reducer;
