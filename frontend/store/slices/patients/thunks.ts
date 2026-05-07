import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import type { RootState } from "@/store";
import {
  PatientListResponse,
  PatientDetail,
  PatientSummary,
  ConditionItem,
  MedicationItem,
  ProcedureItem,
  ImmunizationItem,
  AllergyItem,
  CarePlanItem,
  EncounterItem,
  FetchPatientsArgs,
  PatientResources,
  PagedResponse,
} from "@/models/generic/patients";
import { ErrorResponse } from "@/models/generic/generic";
import { SequenceListItem, PatientContinuationItem } from "@/models/generic/sequences";
import { apiUrl } from "@/utils/apiBases";
import { appendScopeToUrl } from "@/utils/authScope";
import { apiPost, apiPatch, apiDelete } from "@/store/slices/_apiClient";

export interface PatientObservationItem {
  id: number;
  date: string;
  observationCode: string;
  description: string;
  value: string;
  valueNumeric: number | null;
  units: string | null;
  encounterId: string | null;
}

export interface PatientCreatePayload {
  firstName: string;
  lastName: string;
  age: number;
  birthdate?: string | null;
  deathdate?: string | null;
  gender?: string | null;
  race?: string | null;
  ethnicity?: string | null;
  marital?: string | null;
  city?: string | null;
}

export type PatientUpdatePayload = Partial<PatientCreatePayload>;

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

export const fetchPatientResources = createAsyncThunk<
  PatientResources,
  void,
  { state: RootState; rejectValue: ErrorResponse }
>("patients/fetchPatientResources", async (_, thunkAPI) => {
  try {
    return await get<PatientResources>(apiUrl(`/patients/resources`), "patient resources");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient resources" });
  }
}, {
  condition: (_, { getState }) => {
    const s = getState().patients;
    return !s.resourcesLoading && s.resources === null;
  },
});

export const fetchPatients = createAsyncThunk<
  PatientListResponse,
  FetchPatientsArgs,
  { rejectValue: ErrorResponse }
>("patients/fetchPatients", async (args, thunkAPI) => {
  try {
    const q = new URLSearchParams();
    if (args.search) q.set("search", args.search);
    if (args.gender?.length) q.set("gender", args.gender.join(","));
    if (args.ageGroup?.length) q.set("ageGroup", args.ageGroup.join(","));
    if (args.status?.length) q.set("status", args.status.join(","));
    if (args.race?.length) q.set("race", args.race.join(","));
    if (args.marital?.length) q.set("marital", args.marital.join(","));
    if (args.city) q.set("city", args.city);
    q.set("page", args.page.toString());
    q.set("rows", args.rows.toString());
    q.set("sortBy", args.sortBy);
    q.set("sortType", args.sortType);
    return await get<PatientListResponse>(apiUrl(`/patients?${q}`), "patients");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patients" });
  }
});

export const fetchPatientDetail = createAsyncThunk<
  PatientDetail,
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientDetail", async (patientId, thunkAPI) => {
  try {
    return await get<PatientDetail>(apiUrl(`/patients/${patientId}`), "patient");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient" });
  }
});

export const fetchPatientSummary = createAsyncThunk<
  PatientSummary,
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientSummary", async (patientId, thunkAPI) => {
  try {
    return await get<PatientSummary>(apiUrl(`/patients/${patientId}/summary`), "patient summary");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient summary" });
  }
});

export const fetchPatientConditions = createAsyncThunk<
  PagedResponse<ConditionItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientConditions", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<ConditionItem>>(apiUrl(`/patients/${patientId}/conditions?page=${page}`), "conditions");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch conditions" });
  }
});

export const fetchPatientMedications = createAsyncThunk<
  PagedResponse<MedicationItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientMedications", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<MedicationItem>>(apiUrl(`/patients/${patientId}/medications?page=${page}`), "medications");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch medications" });
  }
});

export const fetchPatientProcedures = createAsyncThunk<
  PagedResponse<ProcedureItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientProcedures", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<ProcedureItem>>(apiUrl(`/patients/${patientId}/procedures?page=${page}`), "procedures");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch procedures" });
  }
});

export const fetchPatientImmunizations = createAsyncThunk<
  PagedResponse<ImmunizationItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientImmunizations", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<ImmunizationItem>>(apiUrl(`/patients/${patientId}/immunizations?page=${page}`), "immunizations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch immunizations" });
  }
});

export const fetchPatientAllergies = createAsyncThunk<
  PagedResponse<AllergyItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientAllergies", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<AllergyItem>>(apiUrl(`/patients/${patientId}/allergies?page=${page}`), "allergies");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch allergies" });
  }
});

export const fetchPatientCareplans = createAsyncThunk<
  PagedResponse<CarePlanItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientCareplans", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<CarePlanItem>>(apiUrl(`/patients/${patientId}/careplans?page=${page}`), "careplans");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch careplans" });
  }
});

export const fetchPatientEncounters = createAsyncThunk<
  PagedResponse<EncounterItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientEncounters", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<EncounterItem>>(apiUrl(`/patients/${patientId}/encounters?page=${page}`), "encounters");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch encounters" });
  }
});

export const fetchPatientObservations = createAsyncThunk<
  PagedResponse<PatientObservationItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientObservations", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<PatientObservationItem>>(apiUrl(`/patients/${patientId}/observations?page=${page}`), "observations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch observations" });
  }
});

export const createPatient = createAsyncThunk<
  PatientDetail,
  PatientCreatePayload,
  { rejectValue: ErrorResponse }
>("patients/createPatient", async (payload, thunkAPI) => {
  try {
    return await apiPost<PatientDetail>(apiUrl(`/patients`), payload, "create patient");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to create patient" });
  }
});

export const updatePatient = createAsyncThunk<
  PatientDetail,
  { patientId: string; payload: PatientUpdatePayload },
  { rejectValue: ErrorResponse }
>("patients/updatePatient", async ({ patientId, payload }, thunkAPI) => {
  try {
    return await apiPatch<PatientDetail>(apiUrl(`/patients/${patientId}`), payload, "update patient");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to update patient" });
  }
});

export const deletePatient = createAsyncThunk<
  string,
  string,
  { rejectValue: ErrorResponse }
>("patients/deletePatient", async (patientId, thunkAPI) => {
  try {
    await apiDelete(apiUrl(`/patients/${patientId}`), "delete patient");
    return patientId;
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to delete patient" });
  }
});

export const fetchPatientSequences = createAsyncThunk<
  PagedResponse<SequenceListItem>,
  { patientId: string; page: number },
  { rejectValue: ErrorResponse }
>("patients/fetchPatientSequences", async ({ patientId, page }, thunkAPI) => {
  try {
    return await get<PagedResponse<SequenceListItem>>(apiUrl(`/patients/${patientId}/sequences?page=${page}`), "patient sequences");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient sequences" });
  }
});

export interface FetchPatientContinuationsArgs {
  patientId: string;
  lastN: number;
  page: number;
}

export const fetchPatientContinuations = createAsyncThunk<
  PagedResponse<PatientContinuationItem>,
  FetchPatientContinuationsArgs,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientContinuations", async ({ patientId, lastN, page }, thunkAPI) => {
  try {
    const url = apiUrl(`/patients/${patientId}/sequence-continuations?lastN=${lastN}&page=${page}`);
    return await get<PagedResponse<PatientContinuationItem>>(url, "patient continuations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient continuations" });
  }
});
