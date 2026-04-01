import { createSlice } from "@reduxjs/toolkit";

import { getSqlAgentResponse } from "./thunks";

interface SQLAgentState {
  questions: string[];
  results: string[];
  loading: boolean;
  error: string | null;
}

const initialState: SQLAgentState = {
  questions: [],
  results: [],
  loading: false,
  error: null,
};

const sqlAgentSlice = createSlice({
  name: "sqlAgent",
  initialState,
  reducers: {
    addQuestion: (state, action) => {
      state.questions.push(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getSqlAgentResponse.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getSqlAgentResponse.fulfilled, (state, action) => {
        state.loading = false;
        let cleaned = action.payload
          .trim()
          .replace(/^"|"$/g, "")
          .replace(/```[\w]*\n/g, "")
          .replace(/```/g, "")
          .replace(/\*\*/g, "")
          .replace(/`/g, "")
          .trim();
        state.results.push(cleaned);
      })
      .addCase(getSqlAgentResponse.rejected, (state) => {
        state.loading = false;
        state.error = "Failed to fetch SQL Agent response";
        state.results.push("Sorry, something went wrong. Please try again.");
      });
  },
});

export default sqlAgentSlice.reducer;
export const { addQuestion } = sqlAgentSlice.actions;
