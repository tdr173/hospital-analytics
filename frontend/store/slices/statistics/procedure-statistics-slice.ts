import { createSlice } from "@reduxjs/toolkit";
import { ProcedureStatisticsResponse } from "@/models/generic/statistics";
import { getProceduresStatistics } from "./thunks";

interface ProcedureStatisticsState {
  data: ProcedureStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ProcedureStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const proceduresStatisticsSlice = createSlice({
  name: "proceduresStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getProceduresStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getProceduresStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getProceduresStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default proceduresStatisticsSlice.reducer;
