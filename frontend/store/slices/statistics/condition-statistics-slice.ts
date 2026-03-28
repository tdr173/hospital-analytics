import { createSlice } from "@reduxjs/toolkit";
import { ConditionStatisticsResponse } from "@/models/generic/statistics";
import { getConditionsStatistics } from "./thunks";

interface ConditionStatisticsState {
  data: ConditionStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ConditionStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const conditionsStatisticsSlice = createSlice({
  name: "conditionsStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getConditionsStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getConditionsStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getConditionsStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default conditionsStatisticsSlice.reducer;
