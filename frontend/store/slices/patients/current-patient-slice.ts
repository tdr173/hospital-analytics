import { createSlice, PayloadAction } from "@reduxjs/toolkit";
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
  SequenceListItem,
  PatientContinuationItem,
} from "@/models/generic/sequences";
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
  fetchPatientSequences,
  fetchPatientContinuations,
  fetchPatientObservations,
  PatientObservationItem,
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

interface CurrentPatientState {
  patient: PatientDetail | null;
  summary: PatientSummary | null;
  conditions: PagedCollectionState<ConditionItem>;
  medications: PagedCollectionState<MedicationItem>;
  procedures: PagedCollectionState<ProcedureItem>;
  immunizations: PagedCollectionState<ImmunizationItem>;
  allergies: PagedCollectionState<AllergyItem>;
  careplans: PagedCollectionState<CarePlanItem>;
  encounters: PagedCollectionState<EncounterItem>;
  sequences: PagedCollectionState<SequenceListItem>;
  continuations: PagedCollectionState<PatientContinuationItem>;
  continuationsLastN: number;
  observations: PagedCollectionState<PatientObservationItem>;
  loading: boolean;
  error: string | null;
  loadedTabs: number[];
}

const initialState: CurrentPatientState = {
  patient: null,
  summary: null,
  conditions: initPaged(),
  medications: initPaged(),
  procedures: initPaged(),
  immunizations: initPaged(),
  allergies: initPaged(),
  careplans: initPaged(),
  encounters: initPaged(),
  sequences: initPaged(),
  continuations: initPaged(),
  continuationsLastN: 3,
  observations: initPaged(),
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
    setContinuationsLastN(state, action: PayloadAction<number>) {
      state.continuationsLastN = action.payload;
      // Drop tab 8 from loadedTabs so the page re-fetches with the new N
      // when the user is currently on or returns to that tab.
      state.loadedTabs = state.loadedTabs.filter((t) => t !== 8);
      state.continuations = { items: [], page: 1, hasMore: false, loadingMore: false };
    },
  },
  extraReducers: (builder) => {
    builder
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
      .addCase(fetchPatientSummary.fulfilled, (state, action) => {
        state.summary = action.payload;
      })
      // Conditions (tab 0)
      .addCase(fetchPatientConditions.pending, (state, action) => {
        handlePagedPending(state.conditions, action.meta.arg.page);
      })
      .addCase(fetchPatientConditions.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.conditions, items, hasMore, action.meta.arg.page);
        addTab(state, 0);
      })
      .addCase(fetchPatientConditions.rejected, (state) => {
        handlePagedRejected(state.conditions);
        addTab(state, 0);
      })
      // Medications (tab 1)
      .addCase(fetchPatientMedications.pending, (state, action) => {
        handlePagedPending(state.medications, action.meta.arg.page);
      })
      .addCase(fetchPatientMedications.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.medications, items, hasMore, action.meta.arg.page);
        addTab(state, 1);
      })
      .addCase(fetchPatientMedications.rejected, (state) => {
        handlePagedRejected(state.medications);
        addTab(state, 1);
      })
      // Procedures (tab 2)
      .addCase(fetchPatientProcedures.pending, (state, action) => {
        handlePagedPending(state.procedures, action.meta.arg.page);
      })
      .addCase(fetchPatientProcedures.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.procedures, items, hasMore, action.meta.arg.page);
        addTab(state, 2);
      })
      .addCase(fetchPatientProcedures.rejected, (state) => {
        handlePagedRejected(state.procedures);
        addTab(state, 2);
      })
      // Immunizations (tab 3)
      .addCase(fetchPatientImmunizations.pending, (state, action) => {
        handlePagedPending(state.immunizations, action.meta.arg.page);
      })
      .addCase(fetchPatientImmunizations.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.immunizations, items, hasMore, action.meta.arg.page);
        addTab(state, 3);
      })
      .addCase(fetchPatientImmunizations.rejected, (state) => {
        handlePagedRejected(state.immunizations);
        addTab(state, 3);
      })
      // Allergies (tab 4)
      .addCase(fetchPatientAllergies.pending, (state, action) => {
        handlePagedPending(state.allergies, action.meta.arg.page);
      })
      .addCase(fetchPatientAllergies.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.allergies, items, hasMore, action.meta.arg.page);
        addTab(state, 4);
      })
      .addCase(fetchPatientAllergies.rejected, (state) => {
        handlePagedRejected(state.allergies);
        addTab(state, 4);
      })
      // Careplans (tab 5)
      .addCase(fetchPatientCareplans.pending, (state, action) => {
        handlePagedPending(state.careplans, action.meta.arg.page);
      })
      .addCase(fetchPatientCareplans.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.careplans, items, hasMore, action.meta.arg.page);
        addTab(state, 5);
      })
      .addCase(fetchPatientCareplans.rejected, (state) => {
        handlePagedRejected(state.careplans);
        addTab(state, 5);
      })
      // Encounters (tab 6)
      .addCase(fetchPatientEncounters.pending, (state, action) => {
        handlePagedPending(state.encounters, action.meta.arg.page);
      })
      .addCase(fetchPatientEncounters.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.encounters, items, hasMore, action.meta.arg.page);
        addTab(state, 6);
      })
      .addCase(fetchPatientEncounters.rejected, (state) => {
        handlePagedRejected(state.encounters);
        addTab(state, 6);
      })
      // Sequences (tab 7)
      .addCase(fetchPatientSequences.pending, (state, action) => {
        handlePagedPending(state.sequences, action.meta.arg.page);
      })
      .addCase(fetchPatientSequences.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.sequences, items, hasMore, action.meta.arg.page);
        addTab(state, 7);
      })
      .addCase(fetchPatientSequences.rejected, (state) => {
        handlePagedRejected(state.sequences);
        addTab(state, 7);
      })
      // Continuations (tab 8)
      .addCase(fetchPatientContinuations.pending, (state, action) => {
        handlePagedPending(state.continuations, action.meta.arg.page);
      })
      .addCase(fetchPatientContinuations.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.continuations, items, hasMore, action.meta.arg.page);
        addTab(state, 8);
      })
      .addCase(fetchPatientContinuations.rejected, (state) => {
        handlePagedRejected(state.continuations);
        addTab(state, 8);
      })
      // Observations (tab 9)
      .addCase(fetchPatientObservations.pending, (state, action) => {
        handlePagedPending(state.observations, action.meta.arg.page);
      })
      .addCase(fetchPatientObservations.fulfilled, (state, action) => {
        const { items, hasMore } = action.payload;
        handlePagedFulfilled(state.observations, items, hasMore, action.meta.arg.page);
        addTab(state, 9);
      })
      .addCase(fetchPatientObservations.rejected, (state) => {
        handlePagedRejected(state.observations);
        addTab(state, 9);
      });
  },
});

export const { resetCurrentPatient, setContinuationsLastN } = currentPatientSlice.actions;
export default currentPatientSlice.reducer;
