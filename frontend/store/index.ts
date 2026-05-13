import { configureStore } from "@reduxjs/toolkit";

import patientsStatisticsReducer from "./slices/statistics/patient-statistics-slice";
import encountersStatisticsReducer from "./slices/statistics/encounter-statistics-slice";
import conditionsStatisticsReducer from "./slices/statistics/condition-statistics-slice";
import observationsStatisticsReducer from "./slices/statistics/observation-statistics-slice";
import proceduresStatisticsReducer from "./slices/statistics/procedure-statistics-slice";
import immunizationsStatisticsReducer from "./slices/statistics/immunization-statistics-slice";
import medicationsStatisticsReducer from "./slices/statistics/medication-statistics-slice";
import allergiesStatisticsReducer from "./slices/statistics/allergy-statistics-slice";
import careplansStatisticsReducer from "./slices/statistics/careplan-statistics-slice";
import providersStatisticsReducer from "./slices/statistics/provider-statistics-slice";
import statisticsRangeReducer from "./slices/statistics/range-slice";
import uiReducer from "./slices/ui-slice";
import sqlAgentReducer from "./slices/statistics/sql-agent-slice";
import clustersReducer from "./slices/clusters/clusters-slice";
import pcaScatterReducer from "./slices/clusters/pca-scatter-slice";
import numericalFeaturesReducer from "./slices/clusters/numerical-features-slice";
import categoricalFeaturesReducer from "./slices/clusters/categorical-features-slice";
import aiAnalysisReducer from "./slices/clusters/ai-analysis-slice";
import clusterDetailReducer from "./slices/clusters/cluster-detail-slice";
import sequenceListReducer from "./slices/sequences/sequence-list-slice";
import sequenceResourcesReducer from "./slices/sequences/sequence-resources-slice";
import sequenceAiReducer from "./slices/sequences/sequence-ai-slice";
import patientsReducer from "./slices/patients/patients-slice";
import currentPatientReducer from "./slices/patients/current-patient-slice";
import providersReducer from "./slices/providers/providers-slice";
import currentProviderReducer from "./slices/providers/current-provider-slice";
import dashboardReducer from "./slices/dashboard/dashboard-slice";
import encountersReducer from "./slices/encounters/encounters-slice";
import currentEncounterReducer from "./slices/encounters/current-encounter-slice";
import authReducer from "./slices/auth/auth-slice";
import { usersReducer } from "./slices/users";

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    clusters: clustersReducer,
    pcaScatter: pcaScatterReducer,
    numericalFeatures: numericalFeaturesReducer,
    categoricalFeatures: categoricalFeaturesReducer,
    aiAnalysis: aiAnalysisReducer,
    clusterDetail: clusterDetailReducer,
    sequenceList: sequenceListReducer,
    sequenceResources: sequenceResourcesReducer,
    sequenceAi: sequenceAiReducer,
    patientsStatistics: patientsStatisticsReducer,
    encountersStatistics: encountersStatisticsReducer,
    conditionsStatistics: conditionsStatisticsReducer,
    observationsStatistics: observationsStatisticsReducer,
    proceduresStatistics: proceduresStatisticsReducer,
    immunizationsStatistics: immunizationsStatisticsReducer,
    medicationsStatistics: medicationsStatisticsReducer,
    allergiesStatistics: allergiesStatisticsReducer,
    careplansStatistics: careplansStatisticsReducer,
    providersStatistics: providersStatisticsReducer,
    statisticsRange: statisticsRangeReducer,
    sqlAgent: sqlAgentReducer,
    patients: patientsReducer,
    currentPatient: currentPatientReducer,
    providers: providersReducer,
    currentProvider: currentProviderReducer,
    dashboard: dashboardReducer,
    encounters: encountersReducer,
    currentEncounter: currentEncounterReducer,
    auth: authReducer,
    users: usersReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
