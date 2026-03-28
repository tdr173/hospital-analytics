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

const API_BASE = "http://localhost:8000";

export const getPatientsStatistics = createAsyncThunk<
  PatientStatisticsResponse,
  void,
  { rejectValue: ErrorResponse }
>("getPatientsStatistics", async (_, thunkAPI) => {
  try {
    const response = await fetch(`${API_BASE}/statistics/patients`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch patients statistics",
      });
    }

    return (await response.json()) as PatientStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/encounters`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch encounters statistics",
      });
    }

    return (await response.json()) as EncounterStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/conditions`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch conditions statistics",
      });
    }

    return (await response.json()) as ConditionStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/organizations`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch organizations statistics",
      });
    }

    return (await response.json()) as OrganizationStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/providers`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch providers statistics",
      });
    }

    return (await response.json()) as ProviderStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/allergies`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch allergies statistics",
      });
    }

    return (await response.json()) as AllergyStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/medications`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch medications statistics",
      });
    }

    return (await response.json()) as MedicationStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/procedures`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch procedures statistics",
      });
    }

    return (await response.json()) as ProcedureStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/immunizations`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch immunizations statistics",
      });
    }

    return (await response.json()) as ImmunizationStatisticsResponse;
  } catch (error) {
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
    const response = await fetch(`${API_BASE}/statistics/observations`);

    if (!response.ok) {
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch observations statistics",
      });
    }

    return (await response.json()) as ObservationStatisticsResponse;
  } catch (error) {
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch observations statistics",
    });
  }
});
