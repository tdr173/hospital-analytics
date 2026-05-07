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
  CarePlanStatisticsResponse,
  ProviderStatisticsResponse,
} from "@/models/generic/statistics";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { toast } from "react-toastify";
import { apiUrl } from "@/utils/apiBases";
import { appendScopeToUrl } from "@/utils/authScope";
import { StatisticsRange } from "./range-slice";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

const rangeQuery = (range: StatisticsRange | undefined) =>
  range && range !== "all" ? `?range=${range}` : "";

export const getPatientsStatistics = createAsyncThunk<
  PatientStatisticsResponse,
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getPatientsStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/patients${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getEncountersStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/encounters${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getConditionsStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/conditions${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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

export const getProvidersStatistics = createAsyncThunk<
  ProviderStatisticsResponse,
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getProvidersStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/providers${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getAllergiesStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/allergies${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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

export const getCareplansStatistics = createAsyncThunk<
  CarePlanStatisticsResponse,
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getCareplansStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/careplans${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

    if (!response.ok) {
      toast.error("Failed to load careplans statistics", { toastId: "stat-careplans" });
      return thunkAPI.rejectWithValue({
        error: true,
        message: "Failed to fetch careplans statistics",
      });
    }

    return (await response.json()) as CarePlanStatisticsResponse;
  } catch (error) {
    toast.error("Failed to load careplans statistics", { toastId: "stat-careplans" });
    return thunkAPI.rejectWithValue({
      error: true,
      message: "Failed to fetch careplans statistics",
    });
  }
});

export const getMedicationsStatistics = createAsyncThunk<
  MedicationStatisticsResponse,
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getMedicationsStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/medications${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getProceduresStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/procedures${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getImmunizationsStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/immunizations${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
  StatisticsRange | void,
  { rejectValue: ErrorResponse }
>("getObservationsStatistics", async (range, thunkAPI) => {
  try {
    const response = await fetch(
      apiUrl(`/statistics/observations${rangeQuery(range || undefined)}`),
      { headers: defaultHeaders },
    );

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
    const response = await fetch(appendScopeToUrl(apiUrl(`/statistics/sql-agent`)), {
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
