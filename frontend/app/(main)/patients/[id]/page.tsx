"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";

import { RootState, AppDispatch } from "@/store";
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
} from "@/store/slices/patients/thunks";
import { resetCurrentPatient } from "@/store/slices/patients/current-patient-slice";
import { PatientSummary } from "@/models/generic/patients";

import IdentityCard from "@/components/PatientComponents/PatientIdentityCard/PatientIdentityCard";
import ConditionsTab from "@/components/PatientComponents/ConditionsTab/ConditionsTab";
import MedicationsTab from "@/components/PatientComponents/MedicationsTab/MedicationsTab";
import ProceduresTab from "@/components/PatientComponents/ProceduresTab/ProceduresTab";
import ImmunizationsTab from "@/components/PatientComponents/ImmunizationsTab/ImmunizationsTab";
import AllergiesTab from "@/components/PatientComponents/AllergiesTab/AllergiesTab";
import CarePlansTab from "@/components/PatientComponents/CarePlansTab/CarePlansTab";
import EncountersTab from "@/components/PatientComponents/EncountersTab/EncountersTab";
import SequencesTab from "@/components/PatientComponents/SequencesTab/SequencesTab";

import MetricComponent from "@/components/PatientComponents/MetricComponent/MetricComponent";

import useClasses from "@/utils/useClasses";
import { PatientDetailPageStyles } from "./styles";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

function MetricsRow({ s, classes }: { s: PatientSummary; classes: any }) {
  return (
    <div className={classes.metricsRow}>
      <MetricComponent label="Quality of Life" value={s.qaly} />
      <MetricComponent label="Avg BMI" value={s.avgBmi} unit="kg/m²" />
      <MetricComponent label="Active Conditions" value={s.activeConditions} />
      <MetricComponent label="Total Medications" value={s.totalMedications} />
      <MetricComponent label="Total Procedures" value={s.totalProcedures} />
      <MetricComponent label="Emergency Visits" value={s.emergencyVisits} />
      <MetricComponent label="Days Since Last Visit" value={s.daysSinceLastEncounter} unit="days" />
    </div>
  );
}

const TAB_LABELS = [
  "Conditions",
  "Medications",
  "Procedures",
  "Vaccinations",
  "Allergies",
  "Care Plans",
  "Visits",
  "Care Sequences",
];

const TAB_FETCHERS: Record<number, (id: string) => any> = {
  1: fetchPatientMedications,
  2: fetchPatientProcedures,
  3: fetchPatientImmunizations,
  4: fetchPatientAllergies,
  5: fetchPatientCareplans,
  6: fetchPatientEncounters,
  7: fetchPatientSequences,
};

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const classes = useClasses(PatientDetailPageStyles, {
    name: "PatientDetailPage",
  });

  const {
    patient,
    summary,
    conditions,
    medications,
    procedures,
    immunizations,
    allergies,
    careplans,
    encounters,
    sequences,
    loading,
    error,
    loadedTabs,
  } = useSelector((state: RootState) => state.currentPatient);

  const [tab, setTab] = useState(0);

  useEffect(() => {
    if (!id) return;
    dispatch(resetCurrentPatient());
    dispatch(fetchPatientDetail(id));
    dispatch(fetchPatientSummary(id));
    dispatch(fetchPatientConditions(id));
  }, [id, dispatch]);

  useEffect(() => {
    if (!id || tab === 0 || loadedTabs.includes(tab)) return;
    const fetcher = TAB_FETCHERS[tab];
    if (fetcher) dispatch(fetcher(id));
  }, [tab, id, dispatch, loadedTabs]);

  if (loading) {
    return <div className={classes.pageLoading}>Loading patient profile...</div>;
  }

  if (error || !patient) {
    return (
      <div className={classes.pageError}>{error ?? "Patient not found."}</div>
    );
  }

  const tabContent: Record<number, React.ReactNode> = {
    0: <ConditionsTab data={conditions} />,
    1: <MedicationsTab data={medications} />,
    2: <ProceduresTab data={procedures} />,
    3: <ImmunizationsTab data={immunizations} />,
    4: <AllergiesTab data={allergies} />,
    5: <CarePlansTab data={careplans} />,
    6: <EncountersTab data={encounters} />,
    7: <SequencesTab data={sequences} />,
  };

  return (
    <div className={classes.pageContainer}>
      <IdentityCard patient={patient} classes={classes} />

      {summary && <MetricsRow s={summary} classes={classes} />}

      <div className={classes.tabsPanel}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          variant="fullWidth"
          sx={{
            borderBottom: `1px solid ${theme.colors.border.main}`,
            backgroundColor: theme.colors.surface.containerLow,
            minHeight: 44,
            "& .MuiTab-root": {
              fontFamily: theme.typography.fontFamily,
              fontSize: "0.75rem",
              fontWeight: theme.typography.fontWeight.semibold,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: theme.colors.text.secondary,
              minHeight: 44,
              padding: "0 20px",
              "&.Mui-selected": { color: theme.colors.primary.main },
            },
            "& .MuiTabs-indicator": {
              backgroundColor: theme.colors.primary.main,
              height: 2,
            },
          }}
        >
          {TAB_LABELS.map((label) => (
            <Tab key={label} label={label} disableRipple />
          ))}
        </Tabs>

        <div className={classes.tabContentPadding}>
          {!loadedTabs.includes(tab) ? (
            <div className={classes.tabLoading}>Loading...</div>
          ) : (
            tabContent[tab]
          )}
        </div>
      </div>
    </div>
  );
}
