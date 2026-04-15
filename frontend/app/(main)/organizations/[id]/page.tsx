"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useState } from "react";

import { RootState, AppDispatch } from "@/store";
import {
  fetchOrganizationDetail,
  fetchOrganizationProviders,
  fetchOrganizationEncounters,
} from "@/store/slices/organizations/thunks";
import {
  resetCurrentOrganization,
  setEncountersPage,
} from "@/store/slices/organizations/current-organization-slice";
import { OrganizationProviderItem, OrganizationEncounterItem } from "@/models/generic/organizations";

import useClasses from "@/utils/useClasses";
import { OrganizationDetailPageStyles } from "./styles";
import { clearName, formatDate } from "@/utils/functions";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const ENCOUNTER_CLASS_LABELS: Record<string, string> = {
  inpatient: "Inpatient",
  ambulatory: "Ambulatory",
  wellness: "Wellness",
  emergency: "Emergency",
  urgentcare: "Urgent Care",
};

const ENC_ROWS = 25;

function GenderBadge({ gender, classes }: { gender: string | null; classes: any }) {
  if (!gender) return <span className={classes.genderBadgeEmpty}>-</span>;
  const isFemale = gender === "F";
  return (
    <span className={isFemale ? classes.genderBadgeFemale : classes.genderBadgeMale}>
      {isFemale ? "F" : "M"}
    </span>
  );
}

function ProvidersTab({
  data,
  loading,
  classes,
  onProviderClick,
}: {
  data: OrganizationProviderItem[];
  loading: boolean;
  classes: any;
  onProviderClick: (id: string) => void;
}) {
  if (loading) return <div className={classes.tabLoading}>Loading providers...</div>;
  if (!data.length) return <div className={classes.emptyState}>No providers found.</div>;

  return (
    <div style={{ overflow: "auto", flex: 1 }}>
      <div className={`${classes.gridRow} ${classes.providersGridRow} ${classes.headerRow}`}>
        <div>Name</div>
        <div>Speciality</div>
        <div>Gender</div>
        <div style={{ textAlign: "right" }}>Utilization</div>
      </div>
      {data.map((p, i) => (
        <div
          key={p.providerId}
          className={`${classes.gridRow} ${classes.providersGridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
        >
          <div className={classes.clickableCell} onClick={() => onProviderClick(p.providerId)}>
            {clearName(p.firstName, p.lastName)}
          </div>
          <div className={classes.secondaryText}>{p.speciality ?? "—"}</div>
          <div><GenderBadge gender={p.gender} classes={classes} /></div>
          <div style={{ textAlign: "right", color: theme.colors.text.secondary }}>{p.utilization}</div>
        </div>
      ))}
    </div>
  );
}

function EncountersTab({
  data,
  total,
  page,
  loading,
  classes,
  onPatientClick,
  onProviderClick,
  onPageChange,
}: {
  data: OrganizationEncounterItem[];
  total: number;
  page: number;
  loading: boolean;
  classes: any;
  onPatientClick: (id: string) => void;
  onProviderClick: (id: string) => void;
  onPageChange: (page: number) => void;
}) {
  const totalPages = Math.ceil(total / ENC_ROWS);

  if (loading) return <div className={classes.tabLoading}>Loading encounters...</div>;
  if (!data.length) return <div className={classes.emptyState}>No encounters recorded.</div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0, overflow: "hidden" }}>
      <div style={{ overflow: "auto", flex: 1 }}>
        <div className={`${classes.gridRow} ${classes.encountersGridRow} ${classes.headerRow}`}>
          <div>Patient</div>
          <div>Provider</div>
          <div>Date</div>
          <div>Class</div>
          <div>Description</div>
          <div>Duration</div>
        </div>
        {data.map((r, i) => (
          <div
            key={r.encounterId}
            className={`${classes.gridRow} ${classes.encountersGridRow} ${classes.dataRow} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
          >
            <div className={classes.clickableCell} onClick={() => onPatientClick(r.patientId)}>
              {r.patientName}
            </div>
            <div className={classes.clickableCell} onClick={() => onProviderClick(r.providerId)}>
              {r.providerName}
            </div>
            <div className={classes.secondaryText}>{formatDate(r.startDate)}</div>
            <div>
              <span className={classes.encounterTypeBadge}>
                {ENCOUNTER_CLASS_LABELS[r.encounterClass] ?? r.encounterClass}
              </span>
            </div>
            <div className={classes.secondaryText}>{r.description}</div>
            <div className={classes.secondaryText}>
              {r.duration != null ? `${Math.round(r.duration)} min` : "—"}
            </div>
          </div>
        ))}
      </div>

      <div className={classes.encPaginationRow}>
        <span>
          {(page - 1) * ENC_ROWS + 1}–{Math.min(page * ENC_ROWS, total)} of {total}
        </span>
        <button
          className={classes.encPaginationBtn}
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Prev
        </button>
        <button
          className={classes.encPaginationBtn}
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default function OrganizationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(OrganizationDetailPageStyles, { name: "OrganizationDetailPage" });

  const {
    organization,
    providers,
    encounters,
    encountersTotal,
    encountersPage,
    loading,
    providersLoading,
    encloading,
    error,
  } = useSelector((state: RootState) => state.currentOrganization);

  const [tab, setTab] = useState(0);

  useEffect(() => {
    if (!id) return;
    dispatch(resetCurrentOrganization());
    dispatch(fetchOrganizationDetail(id));
    dispatch(fetchOrganizationProviders(id));
    dispatch(fetchOrganizationEncounters({ organizationId: id, page: 1, rows: ENC_ROWS }));
  }, [id, dispatch]);

  useEffect(() => {
    if (!id) return;
    dispatch(fetchOrganizationEncounters({ organizationId: id, page: encountersPage, rows: ENC_ROWS }));
  }, [encountersPage]);

  const handleEncountersPageChange = (newPage: number) => {
    dispatch(setEncountersPage(newPage));
  };

  if (loading) {
    return <div className={classes.pageLoading}>Loading organization data...</div>;
  }

  if (error || !organization) {
    return <div className={classes.pageError}>{error ?? "Organization not found."}</div>;
  }

  const details = [
    { label: "Phone", value: organization.phone },
    { label: "Utilization", value: String(organization.utilization) },
  ];

  return (
    <div className={classes.pageContainer}>
      <div className={classes.identityCard}>
        <div className={classes.nameBlock}>
          <p className={classes.profileLabel}>Organization Profile</p>
          <h1 className={classes.orgFullName}>{organization.name ?? "Unknown"}</h1>
          <div className={classes.badgesRow}>
            {organization.city && (
              <span className={classes.badge}>{organization.city}</span>
            )}
          </div>
        </div>

        <div className={classes.detailsGrid}>
          {details.map(({ label, value }) => (
            <div key={label}>
              <p className={classes.detailLabel}>{label}</p>
              <p className={classes.detailValue}>{value ?? "—"}</p>
            </div>
          ))}
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
              fontSize: "0.75rem",
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
          <Tab label="Providers" disableRipple />
          <Tab label="Encounters" disableRipple />
        </Tabs>

        <div className={classes.tabContentPadding}>
          {tab === 0 && (
            <ProvidersTab
              data={providers}
              loading={providersLoading}
              classes={classes}
              onProviderClick={(pid) => router.push(`/providers/${pid}`)}
            />
          )}
          {tab === 1 && (
            <EncountersTab
              data={encounters}
              total={encountersTotal}
              page={encountersPage}
              loading={encloading}
              classes={classes}
              onPatientClick={(pid) => router.push(`/patients/${pid}`)}
              onProviderClick={(pid) => router.push(`/providers/${pid}`)}
              onPageChange={handleEncountersPageChange}
            />
          )}
        </div>
      </div>
    </div>
  );
}
