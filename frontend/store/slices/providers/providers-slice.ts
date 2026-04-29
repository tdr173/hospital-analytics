import { createSlice } from "@reduxjs/toolkit";
import { ProviderListItem, ProviderResources } from "@/models/generic/providers";
import { fetchProviders, fetchProviderResources } from "./thunks";

interface ProvidersState {
  items: ProviderListItem[];
  total: number;
  loading: boolean;
  error: string | null;
  resources: ProviderResources | null;
  resourcesLoading: boolean;
}

const initialState: ProvidersState = {
  items: [],
  total: 0,
  loading: true,
  error: null,
  resources: null,
  resourcesLoading: false,
};

const providersSlice = createSlice({
  name: "providers",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProviders.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProviders.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchProviders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      })
      .addCase(fetchProviderResources.pending, (state) => {
        state.resourcesLoading = true;
      })
      .addCase(fetchProviderResources.fulfilled, (state, action) => {
        state.resourcesLoading = false;
        state.resources = action.payload;
      })
      .addCase(fetchProviderResources.rejected, (state) => {
        state.resourcesLoading = false;
      });
  },
});

export default providersSlice.reducer;
