import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { DashboardData, DashboardRange } from "@/models/generic/dashboard";
import { fetchDashboard } from "./thunks";

interface DashboardState {
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  selectedRange: DashboardRange;
}

const initialState: DashboardState = {
  data: null,
  loading: false,
  error: null,
  selectedRange: "month",
};

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {
    setDashboardRange(state, action: PayloadAction<DashboardRange>) {
      if (state.selectedRange !== action.payload) {
        state.selectedRange = action.payload;
        state.data = null; // triggers re-fetch in page useEffect
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboard.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export const { setDashboardRange } = dashboardSlice.actions;
export default dashboardSlice.reducer;
