import { createSlice } from "@reduxjs/toolkit";
import { SequenceResourcesResponse } from "@/models/generic/sequences";
import { fetchSequenceResources } from "./thunks";

interface SequenceResourcesState {
  data: SequenceResourcesResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: SequenceResourcesState = {
  data: null,
  loading: false,
  error: null,
};

const sequenceResourcesSlice = createSlice({
  name: "sequenceResources",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSequenceResources.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSequenceResources.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchSequenceResources.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default sequenceResourcesSlice.reducer;
