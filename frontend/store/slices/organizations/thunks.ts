import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import {
  OrganizationListResponse,
  OrganizationDetail,
  OrganizationProviderItem,
  OrganizationEncounterResponse,
  OrganizationResources,
  FetchOrganizationsArgs,
  FetchOrganizationEncountersArgs,
} from "@/models/generic/organizations";
import { ErrorResponse } from "@/models/generic/generic";
import { API_BASE } from "@/store/slices/clusters/thunks";

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

export const fetchOrganizationResources = createAsyncThunk<
  OrganizationResources,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("organizations/fetchOrganizationResources", async (_, thunkAPI) => {
  try {
    return await get<OrganizationResources>(`${API_BASE}/organizations/resources`, "organization resources");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch organization resources" });
  }
}, {
  condition: (_, { getState }) => {
    const s = getState().organizations;
    return !s.resourcesLoading && s.resources === null;
  },
});

export const fetchOrganizations = createAsyncThunk<
  OrganizationListResponse,
  FetchOrganizationsArgs,
  { rejectValue: ErrorResponse }
>("organizations/fetchOrganizations", async (args, thunkAPI) => {
  try {
    const q = new URLSearchParams();
    if (args.search) q.set("search", args.search);
    if (args.city) q.set("city", args.city);
    q.set("page", args.page.toString());
    q.set("rows", args.rows.toString());
    q.set("sortBy", args.sortBy);
    q.set("sortType", args.sortType);
    return await get<OrganizationListResponse>(`${API_BASE}/organizations?${q}`, "organizations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch organizations" });
  }
});

export const fetchOrganizationDetail = createAsyncThunk<
  OrganizationDetail,
  string,
  { rejectValue: ErrorResponse }
>("organizations/fetchOrganizationDetail", async (organizationId, thunkAPI) => {
  try {
    return await get<OrganizationDetail>(`${API_BASE}/organizations/${organizationId}`, "organization");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch organization" });
  }
});

export const fetchOrganizationProviders = createAsyncThunk<
  OrganizationProviderItem[],
  string,
  { rejectValue: ErrorResponse }
>("organizations/fetchOrganizationProviders", async (organizationId, thunkAPI) => {
  try {
    return await get<OrganizationProviderItem[]>(
      `${API_BASE}/organizations/${organizationId}/providers`,
      "organization providers"
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch organization providers" });
  }
});

export const fetchOrganizationEncounters = createAsyncThunk<
  OrganizationEncounterResponse,
  FetchOrganizationEncountersArgs,
  { rejectValue: ErrorResponse }
>("organizations/fetchOrganizationEncounters", async (args, thunkAPI) => {
  try {
    const q = new URLSearchParams();
    q.set("page", args.page.toString());
    q.set("rows", args.rows.toString());
    return await get<OrganizationEncounterResponse>(
      `${API_BASE}/organizations/${args.organizationId}/encounters?${q}`,
      "organization encounters"
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch organization encounters" });
  }
});
