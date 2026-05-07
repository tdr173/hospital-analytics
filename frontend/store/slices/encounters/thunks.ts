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
import { PagedResponse } from "@/models/generic/patients";
import { ErrorResponse } from "@/models/generic/generic";
import { apiUrl } from "@/utils/apiBases";
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
    return await get<EncounterResources>(apiUrl(`/encounters/resources`), "encounter resources");
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
    return await get<EncounterListResponse>(apiUrl(`/encounters?${q}`), "encounters");
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
    return await get<EncounterDetail>(apiUrl(`/encounters/${encounterId}`), "encounter");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch encounter" });
  }
});

export const fetchEncounterObservations = createAsyncThunk<
  PagedResponse<EncounterObservationItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterObservations", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterObservationItem>>(apiUrl(`/encounters/${encounterId}/observations?page=${page}`), "observations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch observations" });
  }
});

export const fetchEncounterConditions = createAsyncThunk<
  PagedResponse<EncounterConditionItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterConditions", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterConditionItem>>(apiUrl(`/encounters/${encounterId}/conditions?page=${page}`), "conditions");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch conditions" });
  }
});

export const fetchEncounterMedications = createAsyncThunk<
  PagedResponse<EncounterMedicationItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterMedications", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterMedicationItem>>(apiUrl(`/encounters/${encounterId}/medications?page=${page}`), "medications");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch medications" });
  }
});

export const fetchEncounterProcedures = createAsyncThunk<
  PagedResponse<EncounterProcedureItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterProcedures", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterProcedureItem>>(apiUrl(`/encounters/${encounterId}/procedures?page=${page}`), "procedures");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch procedures" });
  }
});

export const fetchEncounterImmunizations = createAsyncThunk<
  PagedResponse<EncounterImmunizationItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterImmunizations", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterImmunizationItem>>(apiUrl(`/encounters/${encounterId}/immunizations?page=${page}`), "immunizations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch immunizations" });
  }
});

export const fetchEncounterAllergies = createAsyncThunk<
  PagedResponse<EncounterAllergyItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterAllergies", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterAllergyItem>>(apiUrl(`/encounters/${encounterId}/allergies?page=${page}`), "allergies");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch allergies" });
  }
});

export const fetchEncounterCareplans = createAsyncThunk<
  PagedResponse<EncounterCarePlanItem>,
  { encounterId: string; page: number },
  { rejectValue: ErrorResponse }
>("encounters/fetchEncounterCareplans", async ({ encounterId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterCarePlanItem>>(apiUrl(`/encounters/${encounterId}/careplans?page=${page}`), "careplans");
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
    return await apiPost<EncounterDetail>(apiUrl(`/encounters`), payload, "create encounter");
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
    return await apiPatch<EncounterDetail>(apiUrl(`/encounters/${encounterId}`), payload, "update encounter");
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
    await apiDelete(apiUrl(`/encounters/${encounterId}`), "delete encounter");
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
      apiUrl(`/encounters/${encounterId}/${PATH_SEG[kind]}`),
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
      apiUrl(`/encounters/${encounterId}/${PATH_SEG[kind]}/${recordId}`),
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
      apiUrl(`/encounters/${encounterId}/${PATH_SEG[kind]}/${recordId}`),
      `delete ${kind}`,
    );
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: `Failed to delete ${kind}` });
  }
});
