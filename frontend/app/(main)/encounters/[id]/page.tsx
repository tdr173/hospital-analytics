"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import IconButton from "@mui/material/IconButton";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AddIcon from "@mui/icons-material/Add";

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
  updateEncounter,
  deleteEncounter,
  createEncounterSubRecord,
  updateEncounterSubRecord,
  deleteEncounterSubRecord,
  SubRecordKind,
} from "@/store/slices/encounters/thunks";
import { resetCurrentEncounter } from "@/store/slices/encounters/current-encounter-slice";

import useClasses from "@/utils/useClasses";
import { EncounterDetailPageStyles } from "./styles";
import { formatDate } from "@/utils/functions";
import theme from "@/utils/theme";

import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import EncounterTag from "@/components/generic_components/EncounterTag/EncounterTag";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import EncounterFormModal, {
  EncounterFormValue,
} from "@/app/(main)/encounters/components/EncounterFormModal/EncounterFormModal";
import SubRecordFormModal from "@/app/(main)/patients/[id]/components/SubRecordFormModal/SubRecordFormModal";

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

const TAB_TO_KIND: Record<number, SubRecordKind> = {
  0: "observation",
  1: "condition",
  2: "medication",
  3: "procedure",
  4: "immunization",
  5: "allergy",
  6: "careplan",
};

const ADD_LABEL: Record<number, string> = {
  0: "Add test result",
  1: "Add condition",
  2: "Add medication",
  3: "Add procedure",
  4: "Add vaccination",
  5: "Add allergy",
  6: "Add care plan",
};

const CODE_FIELD: Record<SubRecordKind, string> = {
  observation: "observationCode",
  condition: "conditionCode",
  medication: "medicationCode",
  procedure: "procedureCode",
  immunization: "immunizationCode",
  careplan: "careplanCode",
  allergy: "allergyCode",
};

interface SubDeleteRef {
  kind: SubRecordKind;
  encounterId: string;
  recordId: number;
}

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

  const role = useSelector((state: RootState) => state.auth.user?.role);
  const canManage = role === "MANAGER" || role === "DOCTOR";

  const [tab, setTab] = useState(0);

  const [encModalOpen, setEncModalOpen] = useState(false);
  const [encDeleting, setEncDeleting] = useState(false);

  const [subModalOpen, setSubModalOpen] = useState(false);
  const [subKind, setSubKind] = useState<SubRecordKind>("condition");
  const [subInitial, setSubInitial] = useState<any | null>(null);
  const [subDeleting, setSubDeleting] = useState<SubDeleteRef | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    dispatch(resetCurrentEncounter());
    dispatch(fetchEncounterDetail(id));
    dispatch(fetchEncounterObservations({ encounterId: id, page: 1 }));
    dispatch(fetchEncounterConditions({ encounterId: id, page: 1 }));
  }, [id, dispatch]);

  useEffect(() => {
    if (!id || tab <= 1 || loadedTabs.includes(tab)) return;
    switch (tab) {
      case 2: dispatch(fetchEncounterMedications({ encounterId: id, page: 1 })); break;
      case 3: dispatch(fetchEncounterProcedures({ encounterId: id, page: 1 })); break;
      case 4: dispatch(fetchEncounterImmunizations({ encounterId: id, page: 1 })); break;
      case 5: dispatch(fetchEncounterAllergies({ encounterId: id, page: 1 })); break;
      case 6: dispatch(fetchEncounterCareplans({ encounterId: id, page: 1 })); break;
    }
  }, [tab, id, dispatch, loadedTabs]);

  const refreshTabData = (tabIndex: number) => {
    if (!id) return;
    switch (tabIndex) {
      case 0: dispatch(fetchEncounterObservations({ encounterId: id, page: 1 })); break;
      case 1: dispatch(fetchEncounterConditions({ encounterId: id, page: 1 })); break;
      case 2: dispatch(fetchEncounterMedications({ encounterId: id, page: 1 })); break;
      case 3: dispatch(fetchEncounterProcedures({ encounterId: id, page: 1 })); break;
      case 4: dispatch(fetchEncounterImmunizations({ encounterId: id, page: 1 })); break;
      case 5: dispatch(fetchEncounterAllergies({ encounterId: id, page: 1 })); break;
      case 6: dispatch(fetchEncounterCareplans({ encounterId: id, page: 1 })); break;
    }
  };

  const handleLoadMore = () => {
    if (!id) return;
    switch (tab) {
      case 0: dispatch(fetchEncounterObservations({ encounterId: id, page: observations.page + 1 })); break;
      case 1: dispatch(fetchEncounterConditions({ encounterId: id, page: conditions.page + 1 })); break;
      case 2: dispatch(fetchEncounterMedications({ encounterId: id, page: medications.page + 1 })); break;
      case 3: dispatch(fetchEncounterProcedures({ encounterId: id, page: procedures.page + 1 })); break;
      case 4: dispatch(fetchEncounterImmunizations({ encounterId: id, page: immunizations.page + 1 })); break;
      case 5: dispatch(fetchEncounterAllergies({ encounterId: id, page: allergies.page + 1 })); break;
      case 6: dispatch(fetchEncounterCareplans({ encounterId: id, page: careplans.page + 1 })); break;
    }
  };

  const pagedByTab = [observations, conditions, medications, procedures, immunizations, allergies, careplans];
  const currentPaged = pagedByTab[tab];

  const handleEncSubmit = async (value: EncounterFormValue) => {
    if (!id) return;
    setSubmitting(true);
    setFormError(null);
    const result = await dispatch(
      updateEncounter({ encounterId: id, payload: value }),
    );
    setSubmitting(false);
    if ((result as any).error) {
      setFormError((result as any).payload?.message ?? "Save failed");
      return;
    }
    setEncModalOpen(false);
    dispatch(fetchEncounterDetail(id));
  };

  const confirmEncDelete = async () => {
    if (!id) return;
    setSubmitting(true);
    const result = await dispatch(deleteEncounter(id));
    setSubmitting(false);
    setEncDeleting(false);
    if (!(result as any).error) router.push("/encounters");
  };

  const openSubAdd = (kind: SubRecordKind) => {
    setSubKind(kind);
    setSubInitial(null);
    setFormError(null);
    setSubModalOpen(true);
  };

  const openSubEdit = (kind: SubRecordKind, record: any) => {
    setSubKind(kind);
    setFormError(null);
    setSubInitial({
      encounterId: id,
      code: record[CODE_FIELD[kind]] ?? "",
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

  if (loading)
    return <div className={classes.pageLoading}>Loading visit details...</div>;
  if (error || !encounter)
    return (
      <div className={classes.pageError}>{error ?? "Visit not found."}</div>
    );

  const encounterForPicker = [encounter as any];

  const tabContent: Record<number, React.ReactNode> = {
    0: (
      <ObservationsTab
        data={observations.items}
        onEdit={
          canManage ? (item) => openSubEdit("observation", item) : undefined
        }
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "observation",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
    1: (
      <ConditionsTab
        data={conditions.items}
        onEdit={
          canManage ? (item) => openSubEdit("condition", item) : undefined
        }
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "condition",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
    2: (
      <MedicationsTab
        data={medications.items}
        onEdit={
          canManage ? (item) => openSubEdit("medication", item) : undefined
        }
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "medication",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
    3: (
      <ProceduresTab
        data={procedures.items}
        onEdit={
          canManage ? (item) => openSubEdit("procedure", item) : undefined
        }
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "procedure",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
    4: (
      <ImmunizationsTab
        data={immunizations.items}
        onEdit={
          canManage ? (item) => openSubEdit("immunization", item) : undefined
        }
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "immunization",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
    5: (
      <AllergiesTab
        data={allergies.items}
        onEdit={canManage ? (item) => openSubEdit("allergy", item) : undefined}
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "allergy",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
    6: (
      <CarePlansTab
        data={careplans.items}
        onEdit={canManage ? (item) => openSubEdit("careplan", item) : undefined}
        onDelete={
          canManage
            ? (item) =>
                setSubDeleting({
                  kind: "careplan",
                  encounterId: id,
                  recordId: item.id,
                })
            : undefined
        }
      />
    ),
  };

  return (
    <div className={classes.pageContainer}>
      <EncounterFormModal
        open={encModalOpen}
        initial={encounter}
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setEncModalOpen(false);
          setFormError(null);
        }}
        onSubmit={handleEncSubmit}
      />

      <FormModal
        open={encDeleting}
        title="Delete visit"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setEncDeleting(false)}
        onSubmit={confirmEncDelete}
        layout="single"
      >
        <div>
          Delete <strong>{encounter.description}</strong>? This cannot be
          undone. Visits with linked records cannot be deleted.
        </div>
      </FormModal>

      <SubRecordFormModal
        open={subModalOpen}
        kind={subKind}
        encounters={encounterForPicker}
        initial={subInitial}
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setSubModalOpen(false);
          setSubInitial(null);
          setFormError(null);
        }}
        onSubmit={handleSubSubmit}
      />

      <FormModal
        open={!!subDeleting}
        title="Delete record"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setSubDeleting(null)}
        onSubmit={confirmSubDelete}
        layout="single"
      >
        <div>Delete this record? This cannot be undone.</div>
      </FormModal>

      <div className={classes.identityCard}>
        <div className={classes.cardLeft}>
          <p className={classes.profileLabel}>Visit Record</p>
          <h1 className={classes.encounterTitle}>{encounter.description}</h1>
          {encounter.reasonDescription && (
            <p className={classes.encounterReason}>
              Reason: {encounter.reasonDescription}
            </p>
          )}
          <div className={classes.metaRow}>
            <EncounterTag type={encounter.encounterClass} />
            {encounter.duration != null && (
              <span className={classes.durationBadge}>
                {Math.round(encounter.duration)} min
              </span>
            )}
            <span className={classes.dateText}>
              {formatDate(encounter.startDate)} →{" "}
              {formatDate(encounter.endDate)}
            </span>
          </div>
        </div>

        <div className={classes.cardRight}>
          <div className={classes.up}>
            <div
              className={classes.entityChip}
              onClick={() => router.push(`/patients/${encounter.patientId}`)}
            >
              <span className={classes.entityChipLabel}>Patient</span>
              <span className={classes.entityChipValue}>
                {encounter.patientName}
              </span>
            </div>
            <div
              className={classes.entityChip}
              onClick={() => router.push(`/providers/${encounter.providerId}`)}
            >
              <span className={classes.entityChipLabel}>Doctor</span>
              <span className={classes.entityChipValue}>
                {encounter.providerName}
              </span>
            </div>
          </div>

          {canManage && (
            <div className={classes.down}>
              {canManage && TAB_TO_KIND[tab] && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    marginBottom: theme.spacing.sm,
                  }}
                >
                  <StyledButton
                    onClick={() => openSubAdd(TAB_TO_KIND[tab])}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-around",
                      height: "40px",
                      minWidth: "160px",
                      background: theme.colors.button.add,
                      boxShadow: "none",
                      border: "none",
                      padding: "0 !important",
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
                </div>
              )}
              {canManage && (
                <div
                  style={{
                    display: "flex",
                    gap: theme.spacing.sm,
                    alignItems: "center",
                    minWidth: "160px",
                    justifyContent: "center",
                    borderRadius: "6px",
                    height: "40px",
                  }}
                >
                  <IconButton
                    size="small"
                    onClick={() => {
                      setFormError(null);
                      setEncModalOpen(true);
                    }}
                    aria-label="Edit visit"
                    sx={{
                      color: theme.colors.text.secondary,
                      "&:hover": { backgroundColor: "rgba(0, 103, 128, 0.08)" },
                    }}
                  >
                    <EditOutlinedIcon sx={{ fontSize: "1.1rem" }} />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => setEncDeleting(true)}
                    aria-label="Delete visit"
                    sx={{
                      color: theme.colors.status.error,
                      "&:hover": { backgroundColor: "rgba(239, 68, 68, 0.08)" },
                    }}
                  >
                    <DeleteOutlineIcon sx={{ fontSize: "1.1rem" }} />
                  </IconButton>
                </div>
              )}
            </div>
          )}
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
    </div>
  );
}
