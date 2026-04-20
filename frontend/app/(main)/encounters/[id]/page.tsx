"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";

import { RootState, AppDispatch } from "@/store";
import {
  fetchEncounterDetail,
  fetchEncounterObservations,
  fetchEncounterConditions,
  fetchEncounterMedications,
  fetchEncounterProcedures,
  fetchEncounterImmunizations,
  fetchEncounterAllergies,
  fetchEncounterCareplans,
} from "@/store/slices/encounters/thunks";
import { resetCurrentEncounter } from "@/store/slices/encounters/current-encounter-slice";

import useClasses from "@/utils/useClasses";
import { EncounterDetailPageStyles } from "./styles";
import { formatDate } from "@/utils/functions";
import theme from "@/utils/theme";

import ObservationsTab from "./components/ObservationsTab/ObservationsTab";
import ConditionsTab from "./components/ConditionsTab/ConditionsTab";
import MedicationsTab from "./components/MedicationsTab/MedicationsTab";
import ProceduresTab from "./components/ProceduresTab/ProceduresTab";
import ImmunizationsTab from "./components/ImmunizationsTab/ImmunizationsTab";
import AllergiesTab from "./components/AllergiesTab/AllergiesTab";
import CarePlansTab from "./components/CarePlansTab/CarePlansTab";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const TAB_LABELS = [
  "Test Results",
  "Conditions",
  "Medications",
  "Procedures",
  "Vaccinations",
  "Allergies",
  "Care Plans",
];

const TAB_FETCHERS: Record<number, (id: string) => any> = {
  2: fetchEncounterMedications,
  3: fetchEncounterProcedures,
  4: fetchEncounterImmunizations,
  5: fetchEncounterAllergies,
  6: fetchEncounterCareplans,
};

export default function EncounterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(EncounterDetailPageStyles, {
    name: "EncounterDetailPage",
  });

  const {
    encounter,
    observations,
    conditions,
    medications,
    procedures,
    immunizations,
    allergies,
    careplans,
    loading,
    error,
    loadedTabs,
  } = useSelector((state: RootState) => state.currentEncounter);

  const [tab, setTab] = useState(0);

  useEffect(() => {
    if (!id) return;
    dispatch(resetCurrentEncounter());
    dispatch(fetchEncounterDetail(id));
    dispatch(fetchEncounterObservations(id));
    dispatch(fetchEncounterConditions(id));
  }, [id, dispatch]);

  useEffect(() => {
    if (!id || tab <= 1 || loadedTabs.includes(tab)) return;
    const fetcher = TAB_FETCHERS[tab];
    if (fetcher) dispatch(fetcher(id));
  }, [tab, id, dispatch, loadedTabs]);

  if (loading) return <div className={classes.pageLoading}>Loading visit details...</div>;
  if (error || !encounter)
    return <div className={classes.pageError}>{error ?? "Visit not found."}</div>;

  const tabContent: Record<number, React.ReactNode> = {
    0: <ObservationsTab data={observations} />,
    1: <ConditionsTab data={conditions} />,
    2: <MedicationsTab data={medications} />,
    3: <ProceduresTab data={procedures} />,
    4: <ImmunizationsTab data={immunizations} />,
    5: <AllergiesTab data={allergies} />,
    6: <CarePlansTab data={careplans} />,
  };

  return (
    <div className={classes.pageContainer}>
      <div className={classes.identityCard}>
        <div className={classes.cardLeft}>
          <p className={classes.profileLabel}>Visit Record</p>
          <h1 className={classes.encounterTitle}>{encounter.description}</h1>
          {encounter.reasonDescription && (
            <p className={classes.encounterReason}>Reason: {encounter.reasonDescription}</p>
          )}
          <div className={classes.metaRow}>
            <span className={classes.classBadge}>{encounter.encounterClass}</span>
            {encounter.duration != null && (
              <span className={classes.durationBadge}>
                {Math.round(encounter.duration)} min
              </span>
            )}
            <span className={classes.dateText}>
              {formatDate(encounter.startDate)} → {formatDate(encounter.endDate)}
            </span>
          </div>
        </div>

        <div className={classes.cardRight}>
          <div
            className={classes.entityChip}
            onClick={() => router.push(`/patients/${encounter.patientId}`)}
          >
            <span className={classes.entityChipLabel}>Patient</span>
            <span className={classes.entityChipValue}>{encounter.patientName}</span>
          </div>
          <div
            className={classes.entityChip}
            onClick={() => router.push(`/providers/${encounter.providerId}`)}
          >
            <span className={classes.entityChipLabel}>Doctor</span>
            <span className={classes.entityChipValue}>{encounter.providerName}</span>
          </div>
          <div
            className={classes.entityChip}
            onClick={() => router.push(`/organizations/${encounter.organizationId}`)}
          >
            <span className={classes.entityChipLabel}>Facility</span>
            <span className={classes.entityChipValue}>
              {encounter.organizationName ?? encounter.organizationId}
            </span>
          </div>
        </div>
      </div>

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
              fontSize: "0.72rem",
              fontWeight: theme.typography.fontWeight.semibold,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: theme.colors.text.secondary,
              minHeight: 44,
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
