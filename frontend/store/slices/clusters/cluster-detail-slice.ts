import { createSlice } from "@reduxjs/toolkit";
import { ClusterDetailResponse } from "@/models/generic/clusters";
import { getClusterDetail } from "./thunks";

interface ClusterDetailState {
  data: ClusterDetailResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ClusterDetailState = {
  data: null,
  loading: false,
  error: null,
};

const clusterDetailSlice = createSlice({
  name: "clusterDetail",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getClusterDetail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getClusterDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(getClusterDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default clusterDetailSlice.reducer;
