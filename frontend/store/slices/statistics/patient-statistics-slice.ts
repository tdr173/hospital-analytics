import { createSlice } from "@reduxjs/toolkit";
import { PatientStatisticsResponse } from "@/models/generic/statistics";
import { getPatientsStatistics } from "./thunks";

interface PatientStatisticsState {
  data: PatientStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: PatientStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const patientsStatisticsSlice = createSlice({
  name: "patientsStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getPatientsStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getPatientsStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getPatientsStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default patientsStatisticsSlice.reducer;
