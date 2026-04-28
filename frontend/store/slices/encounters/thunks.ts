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
import { appendScopeToUrl } from "@/utils/authScope";
import { apiPost, apiPatch, apiDelete } from "@/store/slices/_apiClient";

export type SubRecordKind =
  | "observation"
  | "condition"
  | "medication"
  | "procedure"
  | "immunization"
  | "careplan"
  | "allergy";

const PATH_SEG: Record<SubRecordKind, string> = {
  observation: "observations",
  condition: "conditions",
  medication: "medications",
  procedure: "procedures",
  immunization: "immunizations",
  careplan: "careplans",
  allergy: "allergies",
};

export interface EncounterCreatePayload {
  patientId: string;
  providerId?: string | null;
  startDate: string;
  endDate: string;
  encounterClass: string;
  description: string;
  reasonDescription?: string | null;
}

export type EncounterUpdatePayload = Partial<Omit<EncounterCreatePayload, "patientId">>;

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

export const createEncounter = createAsyncThunk<
  EncounterDetail,
  EncounterCreatePayload,
  { rejectValue: ErrorResponse }
>("encounters/createEncounter", async (payload, thunkAPI) => {
  try {
    return await apiPost<EncounterDetail>(`${API_BASE}/encounters`, payload, "create encounter");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to create encounter" });
  }
});

export const updateEncounter = createAsyncThunk<
  EncounterDetail,
  { encounterId: string; payload: EncounterUpdatePayload },
  { rejectValue: ErrorResponse }
>("encounters/updateEncounter", async ({ encounterId, payload }, thunkAPI) => {
  try {
    return await apiPatch<EncounterDetail>(`${API_BASE}/encounters/${encounterId}`, payload, "update encounter");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to update encounter" });
  }
});

export const deleteEncounter = createAsyncThunk<
  string,
  string,
  { rejectValue: ErrorResponse }
>("encounters/deleteEncounter", async (encounterId, thunkAPI) => {
  try {
    await apiDelete(`${API_BASE}/encounters/${encounterId}`, "delete encounter");
    return encounterId;
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to delete encounter" });
  }
});

export const createEncounterSubRecord = createAsyncThunk<
  unknown,
  { kind: SubRecordKind; encounterId: string; payload: Record<string, unknown> },
  { rejectValue: ErrorResponse }
>("encounters/createSubRecord", async ({ kind, encounterId, payload }, thunkAPI) => {
  try {
    return await apiPost(
      `${API_BASE}/encounters/${encounterId}/${PATH_SEG[kind]}`,
      payload,
      `create ${kind}`,
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: `Failed to create ${kind}` });
  }
});

export const updateEncounterSubRecord = createAsyncThunk<
  unknown,
  { kind: SubRecordKind; encounterId: string; recordId: number; payload: Record<string, unknown> },
  { rejectValue: ErrorResponse }
>("encounters/updateSubRecord", async ({ kind, encounterId, recordId, payload }, thunkAPI) => {
  try {
    return await apiPatch(
      `${API_BASE}/encounters/${encounterId}/${PATH_SEG[kind]}/${recordId}`,
      payload,
      `update ${kind}`,
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: `Failed to update ${kind}` });
  }
});

export const deleteEncounterSubRecord = createAsyncThunk<
  void,
  { kind: SubRecordKind; encounterId: string; recordId: number },
  { rejectValue: ErrorResponse }
>("encounters/deleteSubRecord", async ({ kind, encounterId, recordId }, thunkAPI) => {
  try {
    await apiDelete(
      `${API_BASE}/encounters/${encounterId}/${PATH_SEG[kind]}/${recordId}`,
      `delete ${kind}`,
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: `Failed to delete ${kind}` });
  }
});
