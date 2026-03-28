import { createSlice } from "@reduxjs/toolkit";
import { AllergyStatisticsResponse } from "@/models/generic/statistics";
import { getAllergiesStatistics } from "./thunks";

interface AllergyStatisticsState {
  data: AllergyStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: AllergyStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const allergiesStatisticsSlice = createSlice({
  name: "allergiesStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getAllergiesStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getAllergiesStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getAllergiesStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default allergiesStatisticsSlice.reducer;
