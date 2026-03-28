import { createSlice } from "@reduxjs/toolkit";
import { OrganizationStatisticsResponse } from "@/models/generic/statistics";
import { getOrganizationsStatistics } from "./thunks";

interface OrganizationStatisticsState {
  data: OrganizationStatisticsResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: OrganizationStatisticsState = {
  data: null,
  loading: false,
  error: null,
};

const organizationsStatisticsSlice = createSlice({
  name: "organizationsStatistics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getOrganizationsStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getOrganizationsStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getOrganizationsStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default organizationsStatisticsSlice.reducer;
