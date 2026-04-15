import { createSlice } from "@reduxjs/toolkit";
import {
  PatientDetail,
  PatientSummary,
  ConditionItem,
  MedicationItem,
  ProcedureItem,
  ImmunizationItem,
  AllergyItem,
  CarePlanItem,
  EncounterItem,
} from "@/models/generic/patients";
import {
  fetchPatientDetail,
  fetchPatientSummary,
  fetchPatientConditions,
  fetchPatientMedications,
  fetchPatientProcedures,
  fetchPatientImmunizations,
  fetchPatientAllergies,
  fetchPatientCareplans,
  fetchPatientEncounters,
} from "./thunks";

interface CurrentPatientState {
  patient: PatientDetail | null;
  summary: PatientSummary | null;
  conditions: ConditionItem[];
  medications: MedicationItem[];
  procedures: ProcedureItem[];
  immunizations: ImmunizationItem[];
  allergies: AllergyItem[];
  careplans: CarePlanItem[];
  encounters: EncounterItem[];
  loading: boolean;
  error: string | null;
  loadedTabs: number[];
}

const initialState: CurrentPatientState = {
  patient: null,
  summary: null,
  conditions: [],
  medications: [],
  procedures: [],
  immunizations: [],
  allergies: [],
  careplans: [],
  encounters: [],
  loading: false,
  error: null,
  loadedTabs: [],
};

function addTab(state: CurrentPatientState, index: number) {
  if (!state.loadedTabs.includes(index)) state.loadedTabs.push(index);
}

const currentPatientSlice = createSlice({
  name: "currentPatient",
  initialState,
  reducers: {
    resetCurrentPatient() {
      return { ...initialState, loading: true };
    },
  },
  extraReducers: (builder) => {
    builder
      // Patient detail
      .addCase(fetchPatientDetail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPatientDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.patient = action.payload;
      })
      .addCase(fetchPatientDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Failed to load patient";
      })
      // Summary
      .addCase(fetchPatientSummary.fulfilled, (state, action) => {
        state.summary = action.payload;
      })
      // Conditions (tab 0)
      .addCase(fetchPatientConditions.fulfilled, (state, action) => {
        state.conditions = action.payload;
        addTab(state, 0);
      })
      .addCase(fetchPatientConditions.rejected, (state) => {
        addTab(state, 0);
      })
      // Medications (tab 1)
      .addCase(fetchPatientMedications.fulfilled, (state, action) => {
        state.medications = action.payload;
        addTab(state, 1);
      })
      .addCase(fetchPatientMedications.rejected, (state) => {
        addTab(state, 1);
      })
      // Procedures (tab 2)
      .addCase(fetchPatientProcedures.fulfilled, (state, action) => {
        state.procedures = action.payload;
        addTab(state, 2);
      })
      .addCase(fetchPatientProcedures.rejected, (state) => {
        addTab(state, 2);
      })
      // Immunizations (tab 3)
      .addCase(fetchPatientImmunizations.fulfilled, (state, action) => {
        state.immunizations = action.payload;
        addTab(state, 3);
      })
      .addCase(fetchPatientImmunizations.rejected, (state) => {
        addTab(state, 3);
      })
      // Allergies (tab 4)
      .addCase(fetchPatientAllergies.fulfilled, (state, action) => {
        state.allergies = action.payload;
        addTab(state, 4);
      })
      .addCase(fetchPatientAllergies.rejected, (state) => {
        addTab(state, 4);
      })
      // Careplans (tab 5)
      .addCase(fetchPatientCareplans.fulfilled, (state, action) => {
        state.careplans = action.payload;
        addTab(state, 5);
      })
      .addCase(fetchPatientCareplans.rejected, (state) => {
        addTab(state, 5);
      })
      // Encounters (tab 6)
      .addCase(fetchPatientEncounters.fulfilled, (state, action) => {
        state.encounters = action.payload;
        addTab(state, 6);
      })
      .addCase(fetchPatientEncounters.rejected, (state) => {
        addTab(state, 6);
      });
  },
});

export const { resetCurrentPatient } = currentPatientSlice.actions;
export default currentPatientSlice.reducer;
