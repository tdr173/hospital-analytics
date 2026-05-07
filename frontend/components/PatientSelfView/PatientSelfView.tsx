"use client";

import { useEffect, useState } from "react";
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
  fetchPatientContinuations,
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
import ContinuationsTab from "@/components/PatientComponents/ContinuationsTab/ContinuationsTab";
import MetricComponent from "@/components/PatientComponents/MetricComponent/MetricComponent";
import PersonalLlmSummaryCard from "@/components/PersonalLlmSummaryCard/PersonalLlmSummaryCard";

import useClasses from "@/utils/useClasses";
import { PatientDetailPageStyles } from "@/app/(main)/patients/[id]/styles";
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
  "Possible Continuations",
];

export default function PatientSelfView() {
  const dispatch = useAppDispatch();
  const classes = useClasses(PatientDetailPageStyles, { name: "PatientSelfView" });
  const patientId = useSelector((s: RootState) => s.auth.user?.patientId);

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
    continuations,
    continuationsLastN,
    loading,
    error,
    loadedTabs,
  } = useSelector((state: RootState) => state.currentPatient);

  const [tab, setTab] = useState(0);

  useEffect(() => {
    if (!patientId) return;
    dispatch(resetCurrentPatient());
    dispatch(fetchPatientDetail(patientId));
    dispatch(fetchPatientSummary(patientId));
    dispatch(fetchPatientConditions({ patientId, page: 1 }));
  }, [patientId, dispatch]);

  useEffect(() => {
    if (!patientId || tab === 0 || loadedTabs.includes(tab)) return;
    switch (tab) {
      case 1: dispatch(fetchPatientMedications({ patientId, page: 1 })); break;
      case 2: dispatch(fetchPatientProcedures({ patientId, page: 1 })); break;
      case 3: dispatch(fetchPatientImmunizations({ patientId, page: 1 })); break;
      case 4: dispatch(fetchPatientAllergies({ patientId, page: 1 })); break;
      case 5: dispatch(fetchPatientCareplans({ patientId, page: 1 })); break;
      case 6: dispatch(fetchPatientEncounters({ patientId, page: 1 })); break;
      case 7: dispatch(fetchPatientSequences({ patientId, page: 1 })); break;
      case 8: dispatch(fetchPatientContinuations({ patientId, lastN: continuationsLastN, page: 1 })); break;
    }
  }, [tab, patientId, dispatch, loadedTabs, continuationsLastN]);

  if (!patientId) {
    return <div className={classes.pageError}>No patient id in session.</div>;
  }
  if (loading) {
    return <div className={classes.pageLoading}>Loading your record...</div>;
  }
  if (error || !patient) {
    return <div className={classes.pageError}>{error ?? "Record not found."}</div>;
  }

  const tabContent: Record<number, React.ReactNode> = {
    0: <ConditionsTab data={conditions.items} />,
    1: <MedicationsTab data={medications.items} />,
    2: <ProceduresTab data={procedures.items} />,
    3: <ImmunizationsTab data={immunizations.items} />,
    4: <AllergiesTab data={allergies.items} />,
    5: <CarePlansTab data={careplans.items} />,
    6: <EncountersTab data={encounters.items} />,
    7: <SequencesTab data={sequences.items} />,
    8: <ContinuationsTab patientId={patientId} data={continuations.items} />,
  };

  return (
    <div className={classes.pageContainer}>
      <IdentityCard patient={patient} classes={classes} />
      {summary && <MetricsRow s={summary} classes={classes} />}
      <PersonalLlmSummaryCard />
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
