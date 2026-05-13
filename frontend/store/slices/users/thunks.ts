import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import { apiUrl } from "@/utils/apiBases";
import { apiPatch, apiDelete } from "@/store/slices/_apiClient";
import type { UserRole } from "@/store/slices/auth/thunks";

export interface UserProfileItem {
  userId: number;
  email: string;
  role: UserRole;
  displayName: string | null;
  patientId: string | null;
  providerId: string | null;
  isActive: boolean;
  createdAt: string;
}

export interface UserListResponse {
  items: UserProfileItem[];
  total: number;
}

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

async function get<T>(url: string, label: string): Promise<T> {
  const res = await fetch(url, { headers: defaultHeaders });
  if (!res.ok) {
    toast.error(`Failed to load ${label}`, { toastId: `fetch-${label}` });
    throw new Error(`${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const fetchUsers = createAsyncThunk<
  UserListResponse,
  { page: number; rows: number }
>("users/fetchUsers", async ({ page, rows }, thunkAPI) => {
  try {
    return await get<UserListResponse>(apiUrl(`/users?page=${page}&rows=${rows}`), "users");
  } catch {
    return thunkAPI.rejectWithValue("Failed to fetch users");
  }
});

export const deleteUser = createAsyncThunk<number, number>(
  "users/deleteUser",
  async (userId, thunkAPI) => {
    try {
      await apiDelete(apiUrl(`/users/${userId}`), "delete user");
      return userId;
    } catch {
      return thunkAPI.rejectWithValue("Failed to delete user");
    }
  },
);

export const banUser = createAsyncThunk<UserProfileItem, number>(
  "users/banUser",
  async (userId, thunkAPI) => {
    try {
      return await apiPatch<UserProfileItem>(apiUrl(`/users/${userId}`), { isActive: false }, "ban user");
    } catch {
      return thunkAPI.rejectWithValue("Failed to ban user");
    }
  },
);

export const unbanUser = createAsyncThunk<UserProfileItem, number>(
  "users/unbanUser",
  async (userId, thunkAPI) => {
    try {
      return await apiPatch<UserProfileItem>(apiUrl(`/users/${userId}`), { isActive: true }, "unban user");
    } catch {
      return thunkAPI.rejectWithValue("Failed to unban user");
    }
  },
);
