import { createSlice } from "@reduxjs/toolkit";
import { PcaScatterResponse } from "@/models/generic/clusters";
import { getClusterStatistics } from "./thunks";

interface PcaScatterState {
  data: PcaScatterResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: PcaScatterState = {
  data: null,
  loading: false,
  error: null,
};

const pcaScatterSlice = createSlice({
  name: "pcaScatter",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getClusterStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getClusterStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getClusterStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default pcaScatterSlice.reducer;
