import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import {
  ProviderListResponse,
  ProviderDetail,
  ProviderEncounterItem,
  ProviderResources,
  FetchProvidersArgs,
} from "@/models/generic/providers";
import { ErrorResponse } from "@/models/generic/generic";
import { API_BASE } from "@/store/slices/clusters/thunks";
import { appendScopeToUrl } from "@/utils/authScope";
import { apiPost, apiPatch, apiDelete } from "@/store/slices/_apiClient";

export interface ProviderCreatePayload {
  firstName: string;
  lastName: string;
  gender?: string | null;
  speciality?: string | null;
  city?: string | null;
}

export type ProviderUpdatePayload = Partial<ProviderCreatePayload>;

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

export const fetchProviderResources = createAsyncThunk<
  ProviderResources,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("providers/fetchProviderResources", async (_, thunkAPI) => {
  try {
    return await get<ProviderResources>(`${API_BASE}/providers/resources`, "provider resources");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch provider resources" });
  }
}, {
  condition: (_, { getState }) => {
    const s = getState().providers;
    return !s.resourcesLoading && s.resources === null;
  },
});

export const fetchProviders = createAsyncThunk<
  ProviderListResponse,
  FetchProvidersArgs,
  { rejectValue: ErrorResponse }
>("providers/fetchProviders", async (args, thunkAPI) => {
  try {
    const q = new URLSearchParams();
    if (args.search) q.set("search", args.search);
    if (args.gender?.length) q.set("gender", args.gender.join(","));
    if (args.speciality?.length) q.set("speciality", args.speciality.join(","));
    if (args.city) q.set("city", args.city);
    q.set("page", args.page.toString());
    q.set("rows", args.rows.toString());
    q.set("sortBy", args.sortBy);
    q.set("sortType", args.sortType);
    return await get<ProviderListResponse>(`${API_BASE}/providers?${q}`, "providers");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch providers" });
  }
});

export const fetchProviderDetail = createAsyncThunk<
  ProviderDetail,
  string,
  { rejectValue: ErrorResponse }
>("providers/fetchProviderDetail", async (providerId, thunkAPI) => {
  try {
    return await get<ProviderDetail>(`${API_BASE}/providers/${providerId}`, "provider");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch provider" });
  }
});

export const createProvider = createAsyncThunk<
  ProviderDetail,
  ProviderCreatePayload,
  { rejectValue: ErrorResponse }
>("providers/createProvider", async (payload, thunkAPI) => {
  try {
    return await apiPost<ProviderDetail>(`${API_BASE}/providers`, payload, "create doctor");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to create doctor" });
  }
});

export const updateProvider = createAsyncThunk<
  ProviderDetail,
  { providerId: string; payload: ProviderUpdatePayload },
  { rejectValue: ErrorResponse }
>("providers/updateProvider", async ({ providerId, payload }, thunkAPI) => {
  try {
    return await apiPatch<ProviderDetail>(`${API_BASE}/providers/${providerId}`, payload, "update doctor");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to update doctor" });
  }
});

export const deleteProvider = createAsyncThunk<
  string,
  string,
  { rejectValue: ErrorResponse }
>("providers/deleteProvider", async (providerId, thunkAPI) => {
  try {
    await apiDelete(`${API_BASE}/providers/${providerId}`, "delete doctor");
    return providerId;
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to delete doctor" });
  }
});

export const fetchProviderEncounters = createAsyncThunk<
  ProviderEncounterItem[],
  string,
  { rejectValue: ErrorResponse }
>("providers/fetchProviderEncounters", async (providerId, thunkAPI) => {
  try {
    return await get<ProviderEncounterItem[]>(
      `${API_BASE}/providers/${providerId}/encounters`,
      "provider encounters"
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch provider encounters" });
  }
});
