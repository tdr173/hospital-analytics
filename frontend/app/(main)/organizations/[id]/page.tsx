"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";

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

import useClasses from "@/utils/useClasses";
import { OrganizationDetailPageStyles } from "./styles";
import theme from "@/utils/theme";

import ProvidersTab from "./components/ProvidersTab/ProvidersTab";
import EncountersTab from "./components/EncountersTab/EncountersTab";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();
const ENC_ROWS = 25;

export default function OrganizationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(OrganizationDetailPageStyles, {
    name: "OrganizationDetailPage",
  });

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
    dispatch(
      fetchOrganizationEncounters({ organizationId: id, page: encountersPage, rows: ENC_ROWS }),
    );
  }, [id, encountersPage, dispatch]);

  const handleEncountersPageChange = (newPage: number) => {
    dispatch(setEncountersPage(newPage));
  };

  if (loading) {
    return <div className={classes.pageLoading}>Loading organization data...</div>;
  }
  if (error || !organization) {
    return (
      <div className={classes.pageError}>{error ?? "Organization not found."}</div>
    );
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
            {organization.city && <span className={classes.badge}>{organization.city}</span>}
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
              onProviderClick={(pid) => router.push(`/providers/${pid}`)}
            />
          )}
          {tab === 1 && (
            <EncountersTab
              data={encounters}
              total={encountersTotal}
              page={encountersPage}
              rows={ENC_ROWS}
              loading={encloading}
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
