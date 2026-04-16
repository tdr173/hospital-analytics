import { createSlice } from "@reduxjs/toolkit";
import { EncounterListItem, EncounterResources } from "@/models/generic/encounters";
import { fetchEncounters, fetchEncounterResources } from "./thunks";

interface EncountersState {
  items: EncounterListItem[];
  total: number;
  loading: boolean;
  error: string | null;
  resources: EncounterResources | null;
  resourcesLoading: boolean;
}

const initialState: EncountersState = {
  items: [],
  total: 0,
  loading: true,
  error: null,
  resources: null,
  resourcesLoading: false,
};

const encountersSlice = createSlice({
  name: "encounters",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchEncounters.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchEncounters.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchEncounters.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      })
      .addCase(fetchEncounterResources.pending, (state) => {
        state.resourcesLoading = true;
      })
      .addCase(fetchEncounterResources.fulfilled, (state, action) => {
        state.resourcesLoading = false;
        state.resources = action.payload;
      })
      .addCase(fetchEncounterResources.rejected, (state) => {
        state.resourcesLoading = false;
      });
  },
});

export default encountersSlice.reducer;
