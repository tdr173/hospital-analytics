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
import {
  EncounterObservationItem,
  EncounterConditionItem,
  EncounterMedicationItem,
  EncounterProcedureItem,
  EncounterImmunizationItem,
  EncounterAllergyItem,
  EncounterCarePlanItem,
} from "@/models/generic/encounters";

import useClasses from "@/utils/useClasses";
import { EncounterDetailPageStyles } from "./styles";
import { formatDate } from "@/utils/functions";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const TAB_LABELS = ["Observations", "Conditions", "Medications", "Procedures", "Immunizations", "Allergies", "Care Plans"];

const TAB_FETCHERS: Record<number, (id: string) => any> = {
  2: fetchEncounterMedications,
  3: fetchEncounterProcedures,
  4: fetchEncounterImmunizations,
  5: fetchEncounterAllergies,
  6: fetchEncounterCareplans,
};

// ── Observations ──────────────────────────────────────────────────────────────
function ObservationsTab({ data, classes }: { data: EncounterObservationItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No observations recorded.</div>;

  const maxNumeric = Math.max(...data.map((d) => d.valueNumeric ?? 0), 1);

  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "2fr 1.5fr 80px 110px" }}>
        <div>Description</div>
        <div>Value</div>
        <div>Units</div>
        <div>Date</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "2fr 1.5fr 80px 110px" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.obsValueRow}>
            {r.valueNumeric != null ? (
              <>
                <div
                  className={classes.obsBar}
                  style={{ width: `${Math.max(4, (r.valueNumeric / maxNumeric) * 80)}px` }}
                />
                <span className={classes.cellNumeric}>{r.valueNumeric}</span>
              </>
            ) : (
              <span className={classes.cellSecondary}>{r.value}</span>
            )}
          </div>
          <div className={classes.cellSecondary}>{r.units ?? "—"}</div>
          <div className={classes.cellSecondary}>{formatDate(r.date)}</div>
        </div>
      ))}
    </>
  );
}

// ── Conditions ────────────────────────────────────────────────────────────────
function ConditionsTab({ data, classes }: { data: EncounterConditionItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No conditions recorded.</div>;
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "2.5fr 1fr 110px 80px" }}>
        <div>Description</div>
        <div>Code</div>
        <div>Started</div>
        <div>Status</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "2.5fr 1fr 110px 80px" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.conditionCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div>
            {r.endDate
              ? <span className={classes.badgeResolved}>Resolved</span>
              : <span className={classes.badgeActive}>Active</span>}
          </div>
        </div>
      ))}
    </>
  );
}

// ── Medications ───────────────────────────────────────────────────────────────
function MedicationsTab({ data, classes }: { data: EncounterMedicationItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No medications recorded.</div>;
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "2fr 1fr 100px 100px 80px 1.5fr" }}>
        <div>Description</div>
        <div>Code</div>
        <div>Started</div>
        <div>Ended</div>
        <div>Duration</div>
        <div>Reason</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "2fr 1fr 100px 100px 80px 1.5fr" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.medicationCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>{r.endDate ? formatDate(r.endDate) : "—"}</div>
          <div className={classes.cellSecondary}>
            {r.durationDays != null ? `${Math.round(r.durationDays)}d` : "—"}
          </div>
          <div className={classes.cellSecondary}>{r.reasonDescription ?? "—"}</div>
        </div>
      ))}
    </>
  );
}

// ── Procedures ────────────────────────────────────────────────────────────────
function ProceduresTab({ data, classes }: { data: EncounterProcedureItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No procedures recorded.</div>;
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "2.5fr 1fr 110px 2fr" }}>
        <div>Description</div>
        <div>Code</div>
        <div>Date</div>
        <div>Reason</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "2.5fr 1fr 110px 2fr" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.procedureCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>{r.reasonDescription ?? "—"}</div>
        </div>
      ))}
    </>
  );
}

// ── Immunizations ─────────────────────────────────────────────────────────────
function ImmunizationsTab({ data, classes }: { data: EncounterImmunizationItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No immunizations recorded.</div>;
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "3fr 1fr 120px" }}>
        <div>Description</div>
        <div>Code</div>
        <div>Date</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "3fr 1fr 120px" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.immunizationCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.date)}</div>
        </div>
      ))}
    </>
  );
}

// ── Allergies ─────────────────────────────────────────────────────────────────
function AllergiesTab({ data, classes }: { data: EncounterAllergyItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No allergies recorded.</div>;
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "3fr 1fr 110px 80px" }}>
        <div>Description</div>
        <div>Code</div>
        <div>Recorded</div>
        <div>Status</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "3fr 1fr 110px 80px" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.allergyCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div>
            {r.endDate
              ? <span className={classes.badgeResolved}>Resolved</span>
              : <span className={classes.badgeWarning}>Active</span>}
          </div>
        </div>
      ))}
    </>
  );
}

// ── Care Plans ───────────────────────────────────────────────────────────────
function CarePlansTab({ data, classes }: { data: EncounterCarePlanItem[]; classes: any }) {
  if (!data.length) return <div className={classes.emptyState}>No care plans recorded.</div>;
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: "2.5fr 1fr 110px 2fr" }}>
        <div>Description</div>
        <div>Code</div>
        <div>Date</div>
        <div>Reason</div>
      </div>
      {data.map((r, i) => (
        <div key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          style={{ gridTemplateColumns: "2.5fr 1fr 110px 2fr" }}>
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.careplanCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>{r.reasonDescription ?? "—"}</div>
        </div>
      ))}
    </>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function EncounterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(EncounterDetailPageStyles, { name: "EncounterDetailPage" });

  const {
    encounter, observations, conditions, medications,
    procedures, immunizations, allergies, careplans, loading, error, loadedTabs,
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

  if (loading) return <div className={classes.pageLoading}>Loading encounter data...</div>;
  if (error || !encounter) return <div className={classes.pageError}>{error ?? "Encounter not found."}</div>;

  const tabContent: Record<number, React.ReactNode> = {
    0: <ObservationsTab data={observations} classes={classes} />,
    1: <ConditionsTab data={conditions} classes={classes} />,
    2: <MedicationsTab data={medications} classes={classes} />,
    3: <ProceduresTab data={procedures} classes={classes} />,
    4: <ImmunizationsTab data={immunizations} classes={classes} />,
    5: <AllergiesTab data={allergies} classes={classes} />,
    6: <CarePlansTab data={careplans} classes={classes} />,
  };

  return (
    <div className={classes.pageContainer}>
      {/* Identity card */}
      <div className={classes.identityCard}>
        <div className={classes.cardLeft}>
          <p className={classes.profileLabel}>Encounter Record</p>
          <h1 className={classes.encounterTitle}>{encounter.description}</h1>
          {encounter.reasonDescription && (
            <p className={classes.encounterReason}>Reason: {encounter.reasonDescription}</p>
          )}
          <div className={classes.metaRow}>
            <span className={classes.classBadge}>{encounter.encounterClass}</span>
            {encounter.duration != null && (
              <span className={classes.durationBadge}>{Math.round(encounter.duration)} min</span>
            )}
            <span className={classes.dateText}>
              {formatDate(encounter.startDate)} → {formatDate(encounter.endDate)}
            </span>
          </div>
        </div>

        <div className={classes.cardRight}>
          <div className={classes.entityChip} onClick={() => router.push(`/patients/${encounter.patientId}`)}>
            <span className={classes.entityChipLabel}>Patient</span>
            <span className={classes.entityChipValue}>{encounter.patientName}</span>
          </div>
          <div className={classes.entityChip} onClick={() => router.push(`/providers/${encounter.providerId}`)}>
            <span className={classes.entityChipLabel}>Provider</span>
            <span className={classes.entityChipValue}>{encounter.providerName}</span>
          </div>
          <div className={classes.entityChip} onClick={() => router.push(`/organizations/${encounter.organizationId}`)}>
            <span className={classes.entityChipLabel}>Organization</span>
            <span className={classes.entityChipValue}>{encounter.organizationName ?? encounter.organizationId}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
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
