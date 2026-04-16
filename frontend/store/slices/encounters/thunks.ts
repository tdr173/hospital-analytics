import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import {
  EncounterListResponse,
  EncounterDetail,
  EncounterObservationItem,
  EncounterConditionItem,
  EncounterMedicationItem,
  EncounterProcedureItem,
  EncounterImmunizationItem,
  EncounterAllergyItem,
  EncounterCarePlanItem,
  EncounterResources,
  FetchEncountersArgs,
} from "@/models/generic/encounters";
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

export const fetchEncounterResources = createAsyncThunk<
  EncounterResources,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("encounters/fetchEncounterResources", async (_, thunkAPI) => {
  try {
    return await get<EncounterResources>(`${API_BASE}/encounters/resources`, "encounter resources");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch encounter resources" });
  }
}, {
  condition: (_, { getState }) => {
    const s = getState().encounters;
    return !s.resourcesLoading && s.resources === null;
  },
});

export const fetchEncounters = createAsyncThunk<
  EncounterListResponse,
  FetchEncountersArgs,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounters", async (args, thunkAPI) => {
  try {
    const q = new URLSearchParams();
    if (args.search) q.set("search", args.search);
    if (args.encounterClass?.length) q.set("encounterClass", args.encounterClass.join(","));
    if (args.dateFrom) q.set("dateFrom", args.dateFrom);
    if (args.dateTo) q.set("dateTo", args.dateTo);
    q.set("page", args.page.toString());
    q.set("rows", args.rows.toString());
    q.set("sortBy", args.sortBy);
    q.set("sortType", args.sortType);
    return await get<EncounterListResponse>(`${API_BASE}/encounters?${q}`, "encounters");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch encounters" });
  }
});

export const fetchEncounterDetail = createAsyncThunk<
  EncounterDetail,
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterDetail", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterDetail>(`${API_BASE}/encounters/${encounterId}`, "encounter");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch encounter" });
  }
});

export const fetchEncounterObservations = createAsyncThunk<
  EncounterObservationItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterObservations", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterObservationItem[]>(`${API_BASE}/encounters/${encounterId}/observations`, "observations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch observations" });
  }
});

export const fetchEncounterConditions = createAsyncThunk<
  EncounterConditionItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterConditions", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterConditionItem[]>(`${API_BASE}/encounters/${encounterId}/conditions`, "conditions");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch conditions" });
  }
});

export const fetchEncounterMedications = createAsyncThunk<
  EncounterMedicationItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterMedications", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterMedicationItem[]>(`${API_BASE}/encounters/${encounterId}/medications`, "medications");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch medications" });
  }
});

export const fetchEncounterProcedures = createAsyncThunk<
  EncounterProcedureItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterProcedures", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterProcedureItem[]>(`${API_BASE}/encounters/${encounterId}/procedures`, "procedures");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch procedures" });
  }
});

export const fetchEncounterImmunizations = createAsyncThunk<
  EncounterImmunizationItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterImmunizations", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterImmunizationItem[]>(`${API_BASE}/encounters/${encounterId}/immunizations`, "immunizations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch immunizations" });
  }
});

export const fetchEncounterAllergies = createAsyncThunk<
  EncounterAllergyItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterAllergies", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterAllergyItem[]>(`${API_BASE}/encounters/${encounterId}/allergies`, "allergies");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch allergies" });
  }
});

export const fetchEncounterCareplans = createAsyncThunk<
  EncounterCarePlanItem[],
  string,
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterCareplans", async (encounterId, thunkAPI) => {
  try {
    return await get<EncounterCarePlanItem[]>(`${API_BASE}/encounters/${encounterId}/careplans`, "careplans");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch careplans" });
  }
});
