"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import AddIcon from "@mui/icons-material/Add";

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
  fetchPatientObservations,
  PatientObservationItem,
} from "@/store/slices/patients/thunks";
import {
  createEncounter,
  updateEncounter,
  deleteEncounter,
  createEncounterSubRecord,
  updateEncounterSubRecord,
  deleteEncounterSubRecord,
  SubRecordKind,
} from "@/store/slices/encounters/thunks";
import { resetCurrentPatient } from "@/store/slices/patients/current-patient-slice";
import {
  PatientSummary,
  EncounterItem,
  ConditionItem,
  MedicationItem,
  ProcedureItem,
  ImmunizationItem,
  AllergyItem,
  CarePlanItem,
} from "@/models/generic/patients";

import IdentityCard from "@/components/PatientComponents/PatientIdentityCard/PatientIdentityCard";
import ConditionsTab from "@/components/PatientComponents/ConditionsTab/ConditionsTab";
import MedicationsTab from "@/components/PatientComponents/MedicationsTab/MedicationsTab";
import ProceduresTab from "@/components/PatientComponents/ProceduresTab/ProceduresTab";
import ImmunizationsTab from "@/components/PatientComponents/ImmunizationsTab/ImmunizationsTab";
import AllergiesTab from "@/components/PatientComponents/AllergiesTab/AllergiesTab";
import CarePlansTab from "@/components/PatientComponents/CarePlansTab/CarePlansTab";
import EncountersTab from "@/components/PatientComponents/EncountersTab/EncountersTab";
import SequencesTab from "@/components/PatientComponents/SequencesTab/SequencesTab";
import ObservationsTab from "@/components/PatientComponents/ObservationsTab/ObservationsTab";

import MetricComponent from "@/components/PatientComponents/MetricComponent/MetricComponent";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import EncounterFormModal, {
  EncounterFormValue,
} from "./components/EncounterFormModal/EncounterFormModal";
import SubRecordFormModal from "./components/SubRecordFormModal/SubRecordFormModal";

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
      <MetricComponent
        label="Days Since Last Visit"
        value={s.daysSinceLastEncounter}
        unit="days"
      />
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
  "Sequences",
  "Observations",
];

const TAB_TO_KIND: Record<number, SubRecordKind | null> = {
  0: "condition",
  1: "medication",
  2: "procedure",
  3: "immunization",
  4: "allergy",
  5: "careplan",
  6: null,
  7: null,
  8: "observation",
};

const ADD_LABEL: Record<number, string> = {
  0: "Add condition",
  1: "Add medication",
  2: "Add procedure",
  3: "Add vaccination",
  4: "Add allergy",
  5: "Add care plan",
  6: "Add visit",
  8: "Add observation",
};

interface RecordRef {
  kind: SubRecordKind;
  encounterId: string;
  recordId: number;
  initial: any;
}

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
    observations,
    loading,
    error,
    loadedTabs,
  } = useSelector((state: RootState) => state.currentPatient);
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const chatOpen = useSelector((state: RootState) => state.ui.chatOpen);
  const canManage = role === "MANAGER" || role === "DOCTOR";

  const [tab, setTab] = useState(0);
  const [encModalOpen, setEncModalOpen] = useState(false);
  const [encEditing, setEncEditing] = useState<EncounterItem | null>(null);
  const [encDeleting, setEncDeleting] = useState<EncounterItem | null>(null);
  const [subModalOpen, setSubModalOpen] = useState(false);
  const [subKind, setSubKind] = useState<SubRecordKind>("condition");
  const [subInitial, setSubInitial] = useState<any | null>(null);
  const [subDeleting, setSubDeleting] = useState<RecordRef | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    dispatch(resetCurrentPatient());
    dispatch(fetchPatientDetail(id));
    dispatch(fetchPatientSummary(id));
    dispatch(fetchPatientConditions({ patientId: id, page: 1 }));
    dispatch(fetchPatientEncounters({ patientId: id, page: 1 }));
  }, [id, dispatch]);

  useEffect(() => {
    if (!id || tab === 0 || loadedTabs.includes(tab)) return;
    switch (tab) {
      case 1: dispatch(fetchPatientMedications({ patientId: id, page: 1 })); break;
      case 2: dispatch(fetchPatientProcedures({ patientId: id, page: 1 })); break;
      case 3: dispatch(fetchPatientImmunizations({ patientId: id, page: 1 })); break;
      case 4: dispatch(fetchPatientAllergies({ patientId: id, page: 1 })); break;
      case 5: dispatch(fetchPatientCareplans({ patientId: id, page: 1 })); break;
      case 7: dispatch(fetchPatientSequences({ patientId: id, page: 1 })); break;
      case 8: dispatch(fetchPatientObservations({ patientId: id, page: 1 })); break;
    }
  }, [tab, id, dispatch, loadedTabs]);

  const refreshTabData = (tabIndex: number) => {
    if (!id) return;
    switch (tabIndex) {
      case 0: dispatch(fetchPatientConditions({ patientId: id, page: 1 })); break;
      case 1: dispatch(fetchPatientMedications({ patientId: id, page: 1 })); break;
      case 2: dispatch(fetchPatientProcedures({ patientId: id, page: 1 })); break;
      case 3: dispatch(fetchPatientImmunizations({ patientId: id, page: 1 })); break;
      case 4: dispatch(fetchPatientAllergies({ patientId: id, page: 1 })); break;
      case 5: dispatch(fetchPatientCareplans({ patientId: id, page: 1 })); break;
      case 6: dispatch(fetchPatientEncounters({ patientId: id, page: 1 })); break;
      case 7: dispatch(fetchPatientSequences({ patientId: id, page: 1 })); break;
      case 8: dispatch(fetchPatientObservations({ patientId: id, page: 1 })); break;
    }
    dispatch(fetchPatientSummary(id));
  };

  const refreshEncounters = () => {
    if (!id) return;
    dispatch(fetchPatientEncounters({ patientId: id, page: 1 }));
  };

  const handleLoadMore = () => {
    if (!id) return;
    switch (tab) {
      case 0: dispatch(fetchPatientConditions({ patientId: id, page: conditions.page + 1 })); break;
      case 1: dispatch(fetchPatientMedications({ patientId: id, page: medications.page + 1 })); break;
      case 2: dispatch(fetchPatientProcedures({ patientId: id, page: procedures.page + 1 })); break;
      case 3: dispatch(fetchPatientImmunizations({ patientId: id, page: immunizations.page + 1 })); break;
      case 4: dispatch(fetchPatientAllergies({ patientId: id, page: allergies.page + 1 })); break;
      case 5: dispatch(fetchPatientCareplans({ patientId: id, page: careplans.page + 1 })); break;
      case 6: dispatch(fetchPatientEncounters({ patientId: id, page: encounters.page + 1 })); break;
      case 7: dispatch(fetchPatientSequences({ patientId: id, page: sequences.page + 1 })); break;
      case 8: dispatch(fetchPatientObservations({ patientId: id, page: observations.page + 1 })); break;
    }
  };

  const pagedByTab = [conditions, medications, procedures, immunizations, allergies, careplans, encounters, sequences, observations];
  const currentPaged = pagedByTab[tab];

  const openSubAdd = (kind: SubRecordKind) => {
    setSubKind(kind);
    setSubInitial(null);
    setFormError(null);
    setSubModalOpen(true);
  };

  const openSubEdit = (kind: SubRecordKind, record: any, codeField: string) => {
    if (!record.encounterId) {
      setFormError("Cannot edit: missing encounter link");
      return;
    }
    setSubKind(kind);
    setFormError(null);
    setSubInitial({
      encounterId: record.encounterId,
      code: record[codeField] ?? "",
      description: record.description,
      startDate: record.startDate ?? null,
      endDate: record.endDate ?? null,
      date: record.date ?? null,
      reasonDescription: record.reasonDescription ?? null,
      value: record.value ?? "",
      valueNumeric: record.valueNumeric ?? null,
      units: record.units ?? null,
      _recordId: record.id,
    });
    setSubModalOpen(true);
  };

  const handleSubSubmit = async (
    encounterId: string,
    payload: Record<string, unknown>,
  ) => {
    setSubmitting(true);
    setFormError(null);
    const recordId = subInitial?._recordId as number | undefined;
    const result = await (recordId
      ? dispatch(
          updateEncounterSubRecord({
            kind: subKind,
            encounterId,
            recordId,
            payload,
          }),
        )
      : dispatch(
          createEncounterSubRecord({ kind: subKind, encounterId, payload }),
        ));
    setSubmitting(false);
    if ((result as any).error) {
      setFormError((result as any).payload?.message ?? "Save failed");
      return;
    }
    setSubModalOpen(false);
    setSubInitial(null);
    refreshTabData(tab);
  };

  const confirmSubDelete = async () => {
    if (!subDeleting) return;
    setSubmitting(true);
    const result = await dispatch(
      deleteEncounterSubRecord({
        kind: subDeleting.kind,
        encounterId: subDeleting.encounterId,
        recordId: subDeleting.recordId,
      }),
    );
    setSubmitting(false);
    setSubDeleting(null);
    if (!(result as any).error) refreshTabData(tab);
  };

  const handleEncSubmit = async (value: EncounterFormValue) => {
    if (!id) return;
    setSubmitting(true);
    setFormError(null);
    const result = await (encEditing
      ? dispatch(
          updateEncounter({
            encounterId: encEditing.encounterId,
            payload: value,
          }),
        )
      : dispatch(createEncounter({ patientId: id, ...value })));
    setSubmitting(false);
    if ((result as any).error) {
      setFormError((result as any).payload?.message ?? "Save failed");
      return;
    }
    setEncModalOpen(false);
    setEncEditing(null);
    refreshEncounters();
  };

  const confirmEncDelete = async () => {
    if (!encDeleting) return;
    setSubmitting(true);
    const result = await dispatch(deleteEncounter(encDeleting.encounterId));
    setSubmitting(false);
    setEncDeleting(null);
    if (!(result as any).error) refreshEncounters();
  };

  if (loading) {
    return (
      <div className={classes.pageLoading}>Loading patient profile...</div>
    );
  }

  if (error || !patient) {
    return (
      <div className={classes.pageError}>{error ?? "Patient not found."}</div>
    );
  }

  const renderConditions = () => (
    <ConditionsTab
      data={conditions.items}
      onEdit={
        canManage
          ? (item: ConditionItem) =>
              openSubEdit("condition", item, "conditionCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: ConditionItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "condition",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );
  const renderMedications = () => (
    <MedicationsTab
      data={medications.items}
      onEdit={
        canManage
          ? (item: MedicationItem) =>
              openSubEdit("medication", item, "medicationCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: MedicationItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "medication",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );
  const renderProcedures = () => (
    <ProceduresTab
      data={procedures.items}
      onEdit={
        canManage
          ? (item: ProcedureItem) =>
              openSubEdit("procedure", item, "procedureCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: ProcedureItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "procedure",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );
  const renderImmunizations = () => (
    <ImmunizationsTab
      data={immunizations.items}
      onEdit={
        canManage
          ? (item: ImmunizationItem) =>
              openSubEdit("immunization", item, "immunizationCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: ImmunizationItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "immunization",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );
  const renderAllergies = () => (
    <AllergiesTab
      data={allergies.items}
      onEdit={
        canManage
          ? (item: AllergyItem) => openSubEdit("allergy", item, "allergyCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: AllergyItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "allergy",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );
  const renderCareplans = () => (
    <CarePlansTab
      data={careplans.items}
      onEdit={
        canManage
          ? (item: CarePlanItem) =>
              openSubEdit("careplan", item, "careplanCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: CarePlanItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "careplan",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );
  const renderEncounters = () => (
    <EncountersTab
      data={encounters.items}
      onEdit={
        canManage
          ? (item) => {
              setEncEditing(item);
              setFormError(null);
              setEncModalOpen(true);
            }
          : undefined
      }
      onDelete={canManage ? (item) => setEncDeleting(item) : undefined}
    />
  );
  const renderObservations = () => (
    <ObservationsTab
      data={observations.items}
      onEdit={
        canManage
          ? (item: PatientObservationItem) =>
              openSubEdit("observation", item, "observationCode")
          : undefined
      }
      onDelete={
        canManage
          ? (item: PatientObservationItem) =>
              item.encounterId &&
              setSubDeleting({
                kind: "observation",
                encounterId: item.encounterId,
                recordId: item.id,
                initial: item,
              })
          : undefined
      }
    />
  );

  const tabContent: Record<number, React.ReactNode> = {
    0: renderConditions(),
    1: renderMedications(),
    2: renderProcedures(),
    3: renderImmunizations(),
    4: renderAllergies(),
    5: renderCareplans(),
    6: renderEncounters(),
    7: <SequencesTab data={sequences.items} />,
    8: renderObservations(),
  };

  const handleAddClick = () => {
    if (tab === 6) {
      setEncEditing(null);
      setFormError(null);
      setEncModalOpen(true);
      return;
    }
    const kind = TAB_TO_KIND[tab];
    if (kind) openSubAdd(kind);
  };

  const showAddButton =
    canManage && (tab === 6 || !!TAB_TO_KIND[tab]) && !chatOpen;

  return (
    <div className={classes.pageContainer}>
      <IdentityCard
        patient={patient}
        classes={classes}
        addButton={
          showAddButton && (
            <StyledButton
              onClick={handleAddClick}
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-around",
                height: "32px",
                background: theme.colors.button.add,
                boxShadow: "none",
                border: "none",
                padding: "0 !important",
                minWidth: "0 !important",
                color: "#ffffff",

                animation: "pulseEffect 2.0s infinite ease-in-out",

                "@keyframes pulseEffect": {
                  "0%": {
                    transform: "scale(1)",
                  },
                  "50%": {
                    transform: "scale(1.02)",
                  },
                  "100%": {
                    transform: "scale(1)",
                  },
                },

                "&:hover": {
                  background: theme.colors.button.addHover,
                  boxShadow: "none",
                  transform: "none",
                  animation: "none",
                },
                "&:active": {
                  background: theme.colors.button.addActive,
                  boxShadow: "none",
                  transform: "none",
                },
              }}
            >
              {ADD_LABEL[tab]}
            </StyledButton>
          )
        }
      />

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
            <>
              {tabContent[tab]}
              {currentPaged?.hasMore && (
                <div className={classes.loadMoreRow}>
                  <button
                    className={classes.loadMoreButton}
                    onClick={handleLoadMore}
                    disabled={currentPaged.loadingMore}
                  >
                    {currentPaged.loadingMore ? "Loading..." : "Load more"}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <EncounterFormModal
        open={encModalOpen}
        initial={encEditing}
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setEncModalOpen(false);
          setEncEditing(null);
        }}
        onSubmit={handleEncSubmit}
      />

      <FormModal
        open={!!encDeleting}
        title="Delete visit"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setEncDeleting(null)}
        onSubmit={confirmEncDelete}
        layout="single"
      >
        <div>
          Delete this visit? Records attached to it must be removed first.
        </div>
      </FormModal>

      <SubRecordFormModal
        open={subModalOpen}
        kind={subKind}
        encounters={encounters.items}
        initial={subInitial}
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setSubModalOpen(false);
          setSubInitial(null);
        }}
        onSubmit={handleSubSubmit}
      />

      <FormModal
        open={!!subDeleting}
        title={`Delete ${subDeleting?.kind ?? "record"}`}
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setSubDeleting(null)}
        onSubmit={confirmSubDelete}
        layout="single"
      >
        <div>
          Delete this {subDeleting?.kind} record? This cannot be undone.
        </div>
      </FormModal>
    </div>
  );
}
