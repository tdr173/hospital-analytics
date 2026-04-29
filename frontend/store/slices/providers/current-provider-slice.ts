import { createSlice } from "@reduxjs/toolkit";
import { ProviderDetail, ProviderEncounterItem } from "@/models/generic/providers";
import { fetchProviderDetail, fetchProviderEncounters } from "./thunks";

interface CurrentProviderState {
  provider: ProviderDetail | null;
  encounters: ProviderEncounterItem[];
  loading: boolean;
  encloading: boolean;
  error: string | null;
}

const initialState: CurrentProviderState = {
  provider: null,
  encounters: [],
  loading: false,
  encloading: false,
  error: null,
};

const currentProviderSlice = createSlice({
  name: "currentProvider",
  initialState,
  reducers: {
    resetCurrentProvider() {
      return { ...initialState, loading: true };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProviderDetail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProviderDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.provider = action.payload;
      })
      .addCase(fetchProviderDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Failed to load provider";
      })
      .addCase(fetchProviderEncounters.pending, (state) => {
        state.encloading = true;
      })
      .addCase(fetchProviderEncounters.fulfilled, (state, action) => {
        state.encloading = false;
        state.encounters = action.payload;
      })
      .addCase(fetchProviderEncounters.rejected, (state) => {
        state.encloading = false;
      });
  },
});

export const { resetCurrentProvider } = currentProviderSlice.actions;
export default currentProviderSlice.reducer;
