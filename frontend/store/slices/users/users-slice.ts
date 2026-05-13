import { createSlice } from "@reduxjs/toolkit";
import { fetchUsers, deleteUser, banUser, unbanUser, UserProfileItem } from "./thunks";

interface UsersState {
  items: UserProfileItem[];
  total: number;
  loading: boolean;
  error: string | null;
}

const initialState: UsersState = {
  items: [],
  total: 0,
  loading: false,
  error: null,
};

const usersSlice = createSlice({
  name: "users",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string ?? "Unknown error";
      })
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.items = state.items.filter((u) => u.userId !== action.payload);
        state.total -= 1;
      })
      .addCase(banUser.fulfilled, (state, action) => {
        const i = state.items.findIndex((u) => u.userId === action.payload.userId);
        if (i !== -1) state.items[i] = action.payload;
      })
      .addCase(unbanUser.fulfilled, (state, action) => {
        const i = state.items.findIndex((u) => u.userId === action.payload.userId);
        if (i !== -1) state.items[i] = action.payload;
      });
  },
});

export default usersSlice.reducer;
