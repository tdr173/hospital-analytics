import { createSlice } from "@reduxjs/toolkit";
import { PatientListItem, PatientResources } from "@/models/generic/patients";
import { fetchPatients, fetchPatientResources } from "./thunks";

interface PatientsState {
  items: PatientListItem[];
  total: number;
  loading: boolean;
  error: string | null;
  resources: PatientResources | null;
  resourcesLoading: boolean;
}

const initialState: PatientsState = {
  items: [],
  total: 0,
  loading: false,
  error: null,
  resources: null,
  resourcesLoading: false,
};

const patientsSlice = createSlice({
  name: "patients",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPatients.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPatients.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchPatients.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Unknown error";
      })
      .addCase(fetchPatientResources.pending, (state) => {
        state.resourcesLoading = true;
      })
      .addCase(fetchPatientResources.fulfilled, (state, action) => {
        state.resourcesLoading = false;
        state.resources = action.payload;
      })
      .addCase(fetchPatientResources.rejected, (state) => {
        state.resourcesLoading = false;
      });
  },
});

export default patientsSlice.reducer;
