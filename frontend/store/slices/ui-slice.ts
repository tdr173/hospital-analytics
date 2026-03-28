import { createSlice } from "@reduxjs/toolkit";

interface UiState {
  chatOpen: boolean;
}

const initialState: UiState = {
  chatOpen: false,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleChat(state) {
      state.chatOpen = !state.chatOpen;
    },
  },
});

export const { toggleChat } = uiSlice.actions;
export default uiSlice.reducer;
