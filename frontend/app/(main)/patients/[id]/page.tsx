"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import IdentityCard from "@/components/PatientComponents/PatientIdentityCard/PatientIdentityCard";
import TableCell from "@mui/material/TableCell";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";

import {
  PatientDetail,
  PatientSummary,
  ConditionItem,
  MedicationItem,
  ProcedureItem,
  ImmunizationItem,
  AllergyItem,
  EncounterItem,
} from "@/models/generic/patients";
import { API_BASE } from "@/store/slices/clusters/thunks";
import StyledTable, {
  StyledTableRow,
  bodyCellSx,
} from "@/components/generic_components/StyledTable/StyledTable";
import useClasses from "@/utils/useClasses";
import { PatientDetailPageStyles } from "./styles";
import { formatDate } from "@/utils/functions";
import theme from "@/utils/theme";

import ConditionsTab from "@/components/PatientComponents/ConditionsTab/ConditionsTab";
import MedicationsTab from "@/components/PatientComponents/MedicationsTab/MedicationsTab";
import ProceduresTab from "@/components/PatientComponents/ProceduresTab/ProceduresTab";
import ImmunizationsTab from "@/components/PatientComponents/ImmunizationsTab/ImmunizationsTab";
import AllergiesTab from "@/components/PatientComponents/AllergiesTab/AllergiesTab";
import EncountersTab from "@/components/PatientComponents/EncountersTab/EncountersTab";

const defaultHeaders = { "ngrok-skip-browser-warning": "true" };

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: defaultHeaders });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

const ENCOUNTER_CLASS_LABELS: Record<string, string> = {
  inpatient: "Inpatient",
  ambulatory: "Ambulatory",
  wellness: "Wellness",
  emergency: "Emergency",
  urgentcare: "Urgent Care",
};

// ─── Zone 2: Metrics row ──────────────────────────────────────────────────────
function MetricBox({
  label,
  value,
  unit,
  classes,
}: {
  label: string;
  value: React.ReactNode;
  unit?: string;
  classes: any;
}) {
  return (
    <div className={classes.metricBox}>
      <p className={classes.metricLabel}>{label}</p>
      <p className={classes.metricValue}>
        {value ?? "-"}
        {unit && value !== null && (
          <span className={classes.metricUnit}>{unit}</span>
        )}
      </p>
    </div>
  );
}

function MetricsRow({ s, classes }: { s: PatientSummary; classes: any }) {
  return (
    <div className={classes.metricsRow}>
      <MetricBox label="QALY" value={s.qaly} classes={classes} />
      <MetricBox
        label="Avg BMI"
        value={s.avg_bmi}
        unit="kg/m²"
        classes={classes}
      />
      <MetricBox
        label="Active Conditions"
        value={s.active_conditions}
        classes={classes}
      />
      <MetricBox
        label="Total Medications"
        value={s.total_medications}
        classes={classes}
      />
      <MetricBox
        label="Total Procedures"
        value={s.total_procedures}
        classes={classes}
      />
      <MetricBox
        label="Emergency Visits"
        value={s.emergency_visits}
        classes={classes}
      />
      <MetricBox
        label="Days Since Last Visit"
        value={s.days_since_last_encounter}
        unit="days"
        classes={classes}
      />
    </div>
  );
}

// ─── Zone 3: Medical history tabs ─────────────────────────────────────────────
const TAB_LABELS = [
  "Conditions",
  "Medications",
  "Procedures",
  "Immunizations",
  "Allergies",
  "Encounters",
];

// ─── Main page ────────────────────────────────────────────────────────────────
export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const classes = useClasses(PatientDetailPageStyles, {
    name: "PatientDetailPage",
  });

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [tab, setTab] = useState(0);

  const [conditions, setConditions] = useState<ConditionItem[]>([]);
  const [medications, setMedications] = useState<MedicationItem[]>([]);
  const [procedures, setProcedures] = useState<ProcedureItem[]>([]);
  const [immunizations, setImmunizations] = useState<ImmunizationItem[]>([]);
  const [allergies, setAllergies] = useState<AllergyItem[]>([]);
  const [encounters, setEncounters] = useState<EncounterItem[]>([]);

  const [loadedTabs, setLoadedTabs] = useState<Set<number>>(new Set());
  const [tabLoading, setTabLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch header + summary on mount
  useEffect(() => {
    if (!id) return;
    setPageLoading(true);
    Promise.all([
      apiFetch<PatientDetail>(`/patients/${id}`),
      apiFetch<PatientSummary>(`/patients/${id}/summary`),
    ])
      .then(([p, s]) => {
        setPatient(p);
        setSummary(s);
      })
      .catch(() => setError("Failed to load patient data."))
      .finally(() => setPageLoading(false));
  }, [id]);

  // Lazy-load each tab on first visit
  useEffect(() => {
    if (!id || loadedTabs.has(tab)) return;
    setTabLoading(true);

    const fetchers: Record<number, () => Promise<void>> = {
      0: () =>
        apiFetch<ConditionItem[]>(`/patients/${id}/conditions`).then(
          setConditions,
        ),
      1: () =>
        apiFetch<MedicationItem[]>(`/patients/${id}/medications`).then(
          setMedications,
        ),
      2: () =>
        apiFetch<ProcedureItem[]>(`/patients/${id}/procedures`).then(
          setProcedures,
        ),
      3: () =>
        apiFetch<ImmunizationItem[]>(`/patients/${id}/immunizations`).then(
          setImmunizations,
        ),
      4: () =>
        apiFetch<AllergyItem[]>(`/patients/${id}/allergies`).then(setAllergies),
      5: () =>
        apiFetch<EncounterItem[]>(`/patients/${id}/encounters`).then(
          setEncounters,
        ),
    };

    fetchers[tab]?.()
      .then(() => setLoadedTabs((prev) => new Set(prev).add(tab)))
      .finally(() => setTabLoading(false));
  }, [tab, id, loadedTabs]);

  if (pageLoading) {
    return <div className={classes.pageLoading}>Loading patient data...</div>;
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
    5: <EncountersTab data={encounters} />,
  };

  return (
    <div className={classes.pageContainer}>
      <IdentityCard patient={patient} classes={classes} />

      {/* Zone 2 */}
      {summary && <MetricsRow s={summary} classes={classes} />}

      {/* Zone 3 */}
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
          {tabLoading ? (
            <div className={classes.tabLoading}>Loading...</div>
          ) : (
            tabContent[tab]
          )}
        </div>
      </div>
    </div>
  );
}
