import { createSlice } from "@reduxjs/toolkit";
import {
  EncounterDetail,
  EncounterObservationItem,
  EncounterConditionItem,
  EncounterMedicationItem,
  EncounterProcedureItem,
  EncounterImmunizationItem,
  EncounterAllergyItem,
  EncounterCarePlanItem,
} from "@/models/generic/encounters";
import {
  fetchEncounterDetail,
  fetchEncounterObservations,
  fetchEncounterConditions,
  fetchEncounterMedications,
  fetchEncounterProcedures,
  fetchEncounterImmunizations,
  fetchEncounterAllergies,
  fetchEncounterCareplans,
} from "./thunks";

interface CurrentEncounterState {
  encounter: EncounterDetail | null;
  observations: EncounterObservationItem[];
  conditions: EncounterConditionItem[];
  medications: EncounterMedicationItem[];
  procedures: EncounterProcedureItem[];
  immunizations: EncounterImmunizationItem[];
  allergies: EncounterAllergyItem[];
  careplans: EncounterCarePlanItem[];
  loading: boolean;
  error: string | null;
  loadedTabs: number[];
}

const initialState: CurrentEncounterState = {
  encounter: null,
  observations: [],
  conditions: [],
  medications: [],
  procedures: [],
  immunizations: [],
  allergies: [],
  careplans: [],
  loading: false,
  error: null,
  loadedTabs: [],
};

function addTab(state: CurrentEncounterState, index: number) {
  if (!state.loadedTabs.includes(index)) state.loadedTabs.push(index);
}

const currentEncounterSlice = createSlice({
  name: "currentEncounter",
  initialState,
  reducers: {
    resetCurrentEncounter() {
      return { ...initialState, loading: true };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchEncounterDetail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchEncounterDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.encounter = action.payload;
      })
      .addCase(fetchEncounterDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message ?? "Failed to load encounter";
      })
      .addCase(fetchEncounterObservations.fulfilled, (state, action) => {
        state.observations = action.payload;
        addTab(state, 0);
      })
      .addCase(fetchEncounterObservations.rejected, (state) => { addTab(state, 0); })
      .addCase(fetchEncounterConditions.fulfilled, (state, action) => {
        state.conditions = action.payload;
        addTab(state, 1);
      })
      .addCase(fetchEncounterConditions.rejected, (state) => { addTab(state, 1); })
      .addCase(fetchEncounterMedications.fulfilled, (state, action) => {
        state.medications = action.payload;
        addTab(state, 2);
      })
      .addCase(fetchEncounterMedications.rejected, (state) => { addTab(state, 2); })
      .addCase(fetchEncounterProcedures.fulfilled, (state, action) => {
        state.procedures = action.payload;
        addTab(state, 3);
      })
      .addCase(fetchEncounterProcedures.rejected, (state) => { addTab(state, 3); })
      .addCase(fetchEncounterImmunizations.fulfilled, (state, action) => {
        state.immunizations = action.payload;
        addTab(state, 4);
      })
      .addCase(fetchEncounterImmunizations.rejected, (state) => { addTab(state, 4); })
      .addCase(fetchEncounterAllergies.fulfilled, (state, action) => {
        state.allergies = action.payload;
        addTab(state, 5);
      })
      .addCase(fetchEncounterAllergies.rejected, (state) => { addTab(state, 5); })
      .addCase(fetchEncounterCareplans.fulfilled, (state, action) => {
        state.careplans = action.payload;
        addTab(state, 6);
      })
      .addCase(fetchEncounterCareplans.rejected, (state) => { addTab(state, 6); });
  },
});

export const { resetCurrentEncounter } = currentEncounterSlice.actions;
export default currentEncounterSlice.reducer;
