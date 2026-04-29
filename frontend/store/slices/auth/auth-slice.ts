import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { UserRole } from "./thunks";

export interface AuthUser {
  email: string;
  role: UserRole;
  patientId?: string;
  providerId?: string;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
}

const STORAGE_KEY = "hospitai.auth";

function hydrate(): AuthState {
  if (typeof window === "undefined") {
    return { user: null, isAuthenticated: false };
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { user: null, isAuthenticated: false };
    const parsed = JSON.parse(raw) as AuthUser;
    if (parsed?.email && parsed?.role) {
      return { user: parsed, isAuthenticated: true };
    }
  } catch {
    // malformed json — ignore
  }
  return { user: null, isAuthenticated: false };
}

const authSlice = createSlice({
  name: "auth",
  initialState: hydrate(),
  reducers: {
    login(state, action: PayloadAction<AuthUser>) {
      state.user = action.payload;
      state.isAuthenticated = true;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(action.payload));
      }
    },
    logout(state) {
      state.user = null;
      state.isAuthenticated = false;
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    },
    setScopeIds(
      state,
      action: PayloadAction<{ patientId?: string; providerId?: string }>,
    ) {
      if (!state.user) return;
      if (action.payload.patientId !== undefined) {
        state.user.patientId = action.payload.patientId;
      }
      if (action.payload.providerId !== undefined) {
        state.user.providerId = action.payload.providerId;
      }
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.user));
      }
    },
  },
});

export const { login, logout, setScopeIds } = authSlice.actions;
export default authSlice.reducer;
