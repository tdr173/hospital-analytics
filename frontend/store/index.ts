import { configureStore } from "@reduxjs/toolkit";

import patientsStatisticsReducer from "./slices/statistics/patient-statistics-slice";
import encountersStatisticsReducer from "./slices/statistics/encounter-statistics-slice";
import conditionsStatisticsReducer from "./slices/statistics/condition-statistics-slice";
import observationsStatisticsReducer from "./slices/statistics/observation-statistics-slice";
import proceduresStatisticsReducer from "./slices/statistics/procedure-statistics-slice";
import immunizationsStatisticsReducer from "./slices/statistics/immunization-statistics-slice";
import medicationsStatisticsReducer from "./slices/statistics/medication-statistics-slice";
import allergiesStatisticsReducer from "./slices/statistics/allergy-statistics-slice";
import providersStatisticsReducer from "./slices/statistics/provider-statistics-slice";
import organizationsStatisticsReducer from "./slices/statistics/organization-statistics-slice";
import uiReducer from "./slices/ui-slice";

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    patientsStatistics: patientsStatisticsReducer,
    encountersStatistics: encountersStatisticsReducer,
    conditionsStatistics: conditionsStatisticsReducer,
    observationsStatistics: observationsStatisticsReducer,
    proceduresStatistics: proceduresStatisticsReducer,
    immunizationsStatistics: immunizationsStatisticsReducer,
    medicationsStatistics: medicationsStatisticsReducer,
    allergiesStatistics: allergiesStatisticsReducer,
    providersStatistics: providersStatisticsReducer,
    organizationsStatistics: organizationsStatisticsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
