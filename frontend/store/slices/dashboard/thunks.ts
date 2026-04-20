import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import { DashboardData } from "@/models/generic/dashboard";
import { ErrorResponse } from "@/models/generic/generic";
import { API_BASE } from "@/store/slices/clusters/thunks";
import { appendScopeToUrl } from "@/utils/authScope";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

async function get<T>(url: string, label: string): Promise<T> {
  const scoped = appendScopeToUrl(url);
  const res = await fetch(scoped, { headers: defaultHeaders });
  if (!res.ok) {
    toast.error(`Failed to load ${label}`, { toastId: `fetch-${label}` });
    throw new Error(`${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const fetchDashboard = createAsyncThunk<
  DashboardData,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("dashboard/fetchDashboard", async (_, thunkAPI) => {
  try {
    return await get<DashboardData>(`${API_BASE}/dashboard`, "dashboard");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch dashboard" });
  }
}, {
  condition: (_, { getState }) => !getState().dashboard.loading,
});
