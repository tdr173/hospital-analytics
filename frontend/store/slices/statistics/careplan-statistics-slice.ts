import { createSlice } from "@reduxjs/toolkit";
import { CarePlanStatisticsResponse } from "@/models/generic/statistics";
import { getCareplansStatistics } from "./thunks";

interface CarePlanStatisticsState {
  data: CarePlanStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: CarePlanStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const careplansStatisticsSlice = createSlice({
  name: "careplansStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getCareplansStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getCareplansStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getCareplansStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default careplansStatisticsSlice.reducer;
