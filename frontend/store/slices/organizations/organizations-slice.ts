import { createSlice } from "@reduxjs/toolkit";
import { OrganizationListItem, OrganizationResources } from "@/models/generic/organizations";
import { fetchOrganizations, fetchOrganizationResources } from "./thunks";

interface OrganizationsState {
  items: OrganizationListItem[];
  total: number;
  loading: boolean;
  error: string | null;
  resources: OrganizationResources | null;
  resourcesLoading: boolean;
}

const initialState: OrganizationsState = {
  items: [],
  total: 0,
  loading: false,
  error: null,
  resources: null,
  resourcesLoading: false,
};

const organizationsSlice = createSlice({
  name: "organizations",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrganizations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOrganizations.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchOrganizations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      })
      .addCase(fetchOrganizationResources.pending, (state) => {
        state.resourcesLoading = true;
      })
      .addCase(fetchOrganizationResources.fulfilled, (state, action) => {
        state.resourcesLoading = false;
        state.resources = action.payload;
      })
      .addCase(fetchOrganizationResources.rejected, (state) => {
        state.resourcesLoading = false;
      });
  },
});

export default organizationsSlice.reducer;
