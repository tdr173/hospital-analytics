import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import {
  PatientListResponse,
  PatientDetail,
  PatientSummary,
  ConditionItem,
  MedicationItem,
  ProcedureItem,
  ImmunizationItem,
  AllergyItem,
  EncounterItem,
  FetchPatientsArgs,
  PatientResources,
} from "@/models/generic/patients";
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

export const fetchPatientResources = createAsyncThunk<
  PatientResources,
  void,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientResources", async (_, thunkAPI) => {
  try {
    return await get<PatientResources>(`${API_BASE}/patients/resources`, "patient resources");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient resources" });
  }
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
    return await get<PatientListResponse>(`${API_BASE}/patients?${q}`, "patients");
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
    return await get<PatientDetail>(`${API_BASE}/patients/${patientId}`, "patient");
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
    return await get<PatientSummary>(`${API_BASE}/patients/${patientId}/summary`, "patient summary");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch patient summary" });
  }
});

export const fetchPatientConditions = createAsyncThunk<
  ConditionItem[],
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientConditions", async (patientId, thunkAPI) => {
  try {
    return await get<ConditionItem[]>(`${API_BASE}/patients/${patientId}/conditions`, "conditions");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch conditions" });
  }
});

export const fetchPatientMedications = createAsyncThunk<
  MedicationItem[],
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientMedications", async (patientId, thunkAPI) => {
  try {
    return await get<MedicationItem[]>(`${API_BASE}/patients/${patientId}/medications`, "medications");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch medications" });
  }
});

export const fetchPatientProcedures = createAsyncThunk<
  ProcedureItem[],
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientProcedures", async (patientId, thunkAPI) => {
  try {
    return await get<ProcedureItem[]>(`${API_BASE}/patients/${patientId}/procedures`, "procedures");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch procedures" });
  }
});

export const fetchPatientImmunizations = createAsyncThunk<
  ImmunizationItem[],
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientImmunizations", async (patientId, thunkAPI) => {
  try {
    return await get<ImmunizationItem[]>(`${API_BASE}/patients/${patientId}/immunizations`, "immunizations");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch immunizations" });
  }
});

export const fetchPatientAllergies = createAsyncThunk<
  AllergyItem[],
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientAllergies", async (patientId, thunkAPI) => {
  try {
    return await get<AllergyItem[]>(`${API_BASE}/patients/${patientId}/allergies`, "allergies");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch allergies" });
  }
});

export const fetchPatientEncounters = createAsyncThunk<
  EncounterItem[],
  string,
  { rejectValue: ErrorResponse }
>("patients/fetchPatientEncounters", async (patientId, thunkAPI) => {
  try {
    return await get<EncounterItem[]>(`${API_BASE}/patients/${patientId}/encounters`, "encounters");
  } catch {
    return thunkAPI.rejectWithValue({ error: true, message: "Failed to fetch encounters" });
  }
});
