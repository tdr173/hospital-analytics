import { createSlice } from "@reduxjs/toolkit";
import { EncounterStatisticsResponse } from "@/models/generic/statistics";
import { getEncountersStatistics } from "./thunks";

interface EncounterStatisticsState {
  data: EncounterStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: EncounterStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const encountersStatisticsSlice = createSlice({
  name: "encountersStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getEncountersStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getEncountersStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getEncountersStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default encountersStatisticsSlice.reducer;
