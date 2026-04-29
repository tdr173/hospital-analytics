import { createSlice } from "@reduxjs/toolkit";
import { ClustersResponse } from "@/models/generic/clusters";
import { getClustersOverview } from "./thunks";

interface ClustersState {
  data: ClustersResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: ClustersState = {
  data: null,
  loading: false,
  error: null,
};

const clustersSlice = createSlice({
  name: "clusters",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getClustersOverview.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getClustersOverview.fulfilled, (state, action) => {
        state.loading = false;
        const payload = action.payload;
        const regular = payload.clusters.filter((c) => c.clusterId !== -1);
        const outliers = payload.clusters.filter((c) => c.clusterId === -1);
        state.data = {
          ...payload,
          clusters: [...regular, ...outliers],
        };
      })
      .addCase(getClustersOverview.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default clustersSlice.reducer;
