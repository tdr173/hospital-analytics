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

interface PagedCollectionState<T> {
  items: T[];
  page: number;
  hasMore: boolean;
  loadingMore: boolean;
}

function initPaged<T>(): PagedCollectionState<T> {
  return { items: [], page: 1, hasMore: false, loadingMore: false };
}

function handlePagedPending<T>(state: PagedCollectionState<T>, page: number) {
  if (page > 1) state.loadingMore = true;
}

function handlePagedFulfilled<T>(
  state: PagedCollectionState<T>,
  items: T[],
  hasMore: boolean,
  page: number,
) {
  state.loadingMore = false;
  state.items = page === 1 ? items : [...state.items, ...items];
  state.page = page;
  state.hasMore = hasMore;
}

function handlePagedRejected<T>(state: PagedCollectionState<T>) {
  state.loadingMore = false;
}

interface CurrentEncounterState {
  encounter: EncounterDetail | null;
  observations: PagedCollectionState<EncounterObservationItem>;
  conditions: PagedCollectionState<EncounterConditionItem>;
  medications: PagedCollectionState<EncounterMedicationItem>;
  procedures: PagedCollectionState<EncounterProcedureItem>;
  immunizations: PagedCollectionState<EncounterImmunizationItem>;
  allergies: PagedCollectionState<EncounterAllergyItem>;
  careplans: PagedCollectionState<EncounterCarePlanItem>;
  loading: boolean;
  error: string | null;
  loadedTabs: number[];
}

const initialState: CurrentEncounterState = {
  encounter: null,
  observations: initPaged(),
  conditions: initPaged(),
  medications: initPaged(),
  procedures: initPaged(),
  immunizations: initPaged(),
  allergies: initPaged(),
  careplans: initPaged(),
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
      // Observations (tab 0)
      .addCase(fetchEncounterObservations.pending, (state, action) => {
        handlePagedPending(state.observations, action.meta.arg.page);
      })
      .addCase(fetchEncounterObservations.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.observations, items, hasMore, action.meta.arg.page);
        addTab(state, 0);
      })
      .addCase(fetchEncounterObservations.rejected, (state) => {
        handlePagedRejected(state.observations);
        addTab(state, 0);
      })
      // Conditions (tab 1)
      .addCase(fetchEncounterConditions.pending, (state, action) => {
        handlePagedPending(state.conditions, action.meta.arg.page);
      })
      .addCase(fetchEncounterConditions.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.conditions, items, hasMore, action.meta.arg.page);
        addTab(state, 1);
      })
      .addCase(fetchEncounterConditions.rejected, (state) => {
        handlePagedRejected(state.conditions);
        addTab(state, 1);
      })
      // Medications (tab 2)
      .addCase(fetchEncounterMedications.pending, (state, action) => {
        handlePagedPending(state.medications, action.meta.arg.page);
      })
      .addCase(fetchEncounterMedications.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.medications, items, hasMore, action.meta.arg.page);
        addTab(state, 2);
      })
      .addCase(fetchEncounterMedications.rejected, (state) => {
        handlePagedRejected(state.medications);
        addTab(state, 2);
      })
      // Procedures (tab 3)
      .addCase(fetchEncounterProcedures.pending, (state, action) => {
        handlePagedPending(state.procedures, action.meta.arg.page);
      })
      .addCase(fetchEncounterProcedures.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.procedures, items, hasMore, action.meta.arg.page);
        addTab(state, 3);
      })
      .addCase(fetchEncounterProcedures.rejected, (state) => {
        handlePagedRejected(state.procedures);
        addTab(state, 3);
      })
      // Immunizations (tab 4)
      .addCase(fetchEncounterImmunizations.pending, (state, action) => {
        handlePagedPending(state.immunizations, action.meta.arg.page);
      })
      .addCase(fetchEncounterImmunizations.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.immunizations, items, hasMore, action.meta.arg.page);
        addTab(state, 4);
      })
      .addCase(fetchEncounterImmunizations.rejected, (state) => {
        handlePagedRejected(state.immunizations);
        addTab(state, 4);
      })
      // Allergies (tab 5)
      .addCase(fetchEncounterAllergies.pending, (state, action) => {
        handlePagedPending(state.allergies, action.meta.arg.page);
      })
      .addCase(fetchEncounterAllergies.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.allergies, items, hasMore, action.meta.arg.page);
        addTab(state, 5);
      })
      .addCase(fetchEncounterAllergies.rejected, (state) => {
        handlePagedRejected(state.allergies);
        addTab(state, 5);
      })
      // Careplans (tab 6)
      .addCase(fetchEncounterCareplans.pending, (state, action) => {
        handlePagedPending(state.careplans, action.meta.arg.page);
      })
      .addCase(fetchEncounterCareplans.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.careplans, items, hasMore, action.meta.arg.page);
        addTab(state, 6);
      })
      .addCase(fetchEncounterCareplans.rejected, (state) => {
        handlePagedRejected(state.careplans);
        addTab(state, 6);
      });
  },
});

export const { resetCurrentEncounter } = currentEncounterSlice.actions;
export default currentEncounterSlice.reducer;
