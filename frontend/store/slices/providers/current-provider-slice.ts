import { createSlice } from "@reduxjs/toolkit";
import { ProviderDetail, ProviderEncounterItem } from "@/models/generic/providers";
import { fetchProviderDetail, fetchProviderEncounters } from "./thunks";

interface CurrentProviderState {
  provider: ProviderDetail | null;
  encounters: ProviderEncounterItem[];
  encPage: number;
  encHasMore: boolean;
  loading: boolean;
  encloading: boolean;
  encLoadingMore: boolean;
  error: string | null;
}

const initialState: CurrentProviderState = {
  provider: null,
  encounters: [],
  encPage: 1,
  encHasMore: false,
  loading: false,
  encloading: false,
  encLoadingMore: false,
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
      .addCase(fetchProviderEncounters.pending, (state, action) => {
        if (action.meta.arg.page === 1) {
          state.encloading = true;
        } else {
          state.encLoadingMore = true;
        }
      })
      .addCase(fetchProviderEncounters.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        const page = action.meta.arg.page;
        state.encloading = false;
        state.encLoadingMore = false;
        state.encounters = page === 1 ? items : [...state.encounters, ...items];
        state.encPage = page;
        state.encHasMore = hasMore;
      })
      .addCase(fetchProviderEncounters.rejected, (state) => {
        state.encloading = false;
        state.encLoadingMore = false;
      });
  },
});

export const { resetCurrentProvider } = currentProviderSlice.actions;
export default currentProviderSlice.reducer;
