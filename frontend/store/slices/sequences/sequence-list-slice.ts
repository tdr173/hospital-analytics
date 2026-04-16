import { createSlice } from "@reduxjs/toolkit";
import { SequenceListResponse } from "@/models/generic/sequences";
import { fetchSequences } from "./thunks";

interface SequenceListState {
  data: SequenceListResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: SequenceListState = {
  data: null,
  loading: false,
  error: null,
};

const sequenceListSlice = createSlice({
  name: "sequenceList",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSequences.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSequences.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchSequences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      });
  },
});

export default sequenceListSlice.reducer;
