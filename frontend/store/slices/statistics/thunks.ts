import { ErrorResponse } from "@/models/generic/generic";
import {
  PatientStatisticsResponse,
  EncounterStatisticsResponse,
  ConditionStatisticsResponse,
  ObservationStatisticsResponse,
  ProcedureStatisticsResponse,
  ImmunizationStatisticsResponse,
  MedicationStatisticsResponse,
  AllergyStatisticsResponse,
  ProviderStatisticsResponse,
  OrganizationStatisticsResponse,
} from "@/models/generic/statistics";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";

const API_BASE = "http://localhost:8000";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export const getPatientsStatistics = createAsyncThunk<
  PatientStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getPatientsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/patients`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load patients statistics", { toastId: "stat-patients" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch patients statistics",
      });
    }

    return (await response.json()) as PatientStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load patients statistics", { toastId: "stat-patients" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch patients statistics",
    });
  }
});

export const getEncountersStatistics = createAsyncThunk<
  EncounterStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getEncountersStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/encounters`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load encounters statistics", { toastId: "stat-encounters" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch encounters statistics",
      });
    }

    return (await response.json()) as EncounterStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load encounters statistics", { toastId: "stat-encounters" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch encounters statistics",
    });
  }
});

export const getConditionsStatistics = createAsyncThunk<
  ConditionStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getConditionsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/conditions`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load conditions statistics", { toastId: "stat-conditions" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch conditions statistics",
      });
    }

    return (await response.json()) as ConditionStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load conditions statistics", { toastId: "stat-conditions" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch conditions statistics",
    });
  }
});

export const getOrganizationsStatistics = createAsyncThunk<
  OrganizationStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getOrganizationsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/organizations`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load organizations statistics", { toastId: "stat-organizations" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch organizations statistics",
      });
    }

    return (await response.json()) as OrganizationStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load organizations statistics", { toastId: "stat-organizations" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch organizations statistics",
    });
  }
});

export const getProvidersStatistics = createAsyncThunk<
  ProviderStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getProvidersStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/providers`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load providers statistics", { toastId: "stat-providers" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch providers statistics",
      });
    }

    return (await response.json()) as ProviderStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load providers statistics", { toastId: "stat-providers" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch providers statistics",
    });
  }
});

export const getAllergiesStatistics = createAsyncThunk<
  AllergyStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getAllergiesStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/allergies`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load allergies statistics", { toastId: "stat-allergies" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch allergies statistics",
      });
    }

    return (await response.json()) as AllergyStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load allergies statistics", { toastId: "stat-allergies" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch allergies statistics",
    });
  }
});

export const getMedicationsStatistics = createAsyncThunk<
  MedicationStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getMedicationsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/medications`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load medications statistics", { toastId: "stat-medications" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch medications statistics",
      });
    }

    return (await response.json()) as MedicationStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load medications statistics", { toastId: "stat-medications" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch medications statistics",
    });
  }
});

export const getProceduresStatistics = createAsyncThunk<
  ProcedureStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getProceduresStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/procedures`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load procedures statistics", { toastId: "stat-procedures" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch procedures statistics",
      });
    }

    return (await response.json()) as ProcedureStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load procedures statistics", { toastId: "stat-procedures" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch procedures statistics",
    });
  }
});

export const getImmunizationsStatistics = createAsyncThunk<
  ImmunizationStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getImmunizationsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/immunizations`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load immunizations statistics", { toastId: "stat-immunizations" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch immunizations statistics",
      });
    }

    return (await response.json()) as ImmunizationStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load immunizations statistics", { toastId: "stat-immunizations" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch immunizations statistics",
    });
  }
});

export const getObservationsStatistics = createAsyncThunk<
  ObservationStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getObservationsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/observations`, {
      headers: defaultHeaders,
    });

    if (!response.ok) {
      toast.error("Failed to load observations statistics", { toastId: "stat-observations" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch observations statistics",
      });
    }

    return (await response.json()) as ObservationStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load observations statistics", { toastId: "stat-observations" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch observations statistics",
    });
  }
});

export const getSqlAgentResponse = createAsyncThunk<
  string,
  { question: string; history: { role: string; content: string }[] },
  { rejectValue: ErrorResponse }
>("getSqlAgentResponse", async ({ question, history }, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/sql-agent`, {
      method: "POST",
      headers: {
        ...defaultHeaders,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, history }),
    });

    if (!response.ok) {
      toast.error("Failed to get SQL agent response", { toastId: "stat-sql-agent" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to get SQL agent response",
      });
    }

    const data = await response.json();
    return data.response as string;
  } catch (error) {
    toast.error("Failed to get SQL agent response", { toastId: "stat-sql-agent" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to get SQL agent response",
    });
  }
});
