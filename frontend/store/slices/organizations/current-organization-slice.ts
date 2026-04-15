import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  OrganizationDetail,
  OrganizationProviderItem,
  OrganizationEncounterItem,
} from "@/models/generic/organizations";
import {
  fetchOrganizationDetail,
  fetchOrganizationProviders,
  fetchOrganizationEncounters,
} from "./thunks";

interface CurrentOrganizationState {
  organization: OrganizationDetail | null;
  providers: OrganizationProviderItem[];
  encounters: OrganizationEncounterItem[];
  encountersTotal: number;
  encountersPage: number;
  loading: boolean;
  providersLoading: boolean;
  encloading: boolean;
  error: string | null;
}

const initialState: CurrentOrganizationState = {
  organization: null,
  providers: [],
  encounters: [],
  encountersTotal: 0,
  encountersPage: 1,
  loading: false,
  providersLoading: false,
  encloading: false,
  error: null,
};

const currentOrganizationSlice = createSlice({
  name: "currentOrganization",
  initialState,
  reducers: {
    resetCurrentOrganization() {
      return { ...initialState, loading: true };
    },
    setEncountersPage(state, action: PayloadAction<number>) {
      state.encountersPage = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrganizationDetail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOrganizationDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.organization = action.payload;
      })
      .addCase(fetchOrganizationDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Failed to load organization";
      })
      .addCase(fetchOrganizationProviders.pending, (state) => {
        state.providersLoading = true;
      })
      .addCase(fetchOrganizationProviders.fulfilled, (state, action) => {
        state.providersLoading = false;
        state.providers = action.payload;
      })
      .addCase(fetchOrganizationProviders.rejected, (state) => {
        state.providersLoading = false;
      })
      .addCase(fetchOrganizationEncounters.pending, (state) => {
        state.encloading = true;
      })
      .addCase(fetchOrganizationEncounters.fulfilled, (state, action) => {
        state.encloading = false;
        state.encounters = action.payload.items;
        state.encountersTotal = action.payload.total;
      })
      .addCase(fetchOrganizationEncounters.rejected, (state) => {
        state.encloading = false;
      });
  },
});

export const { resetCurrentOrganization, setEncountersPage } = currentOrganizationSlice.actions;
export default currentOrganizationSlice.reducer;
