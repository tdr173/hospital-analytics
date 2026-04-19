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
import { resetCurrentOrganization } from "@/store/slices/organizations/current-organization-slice";

import useClasses from "@/utils/useClasses";
import { OrganizationDetailPageStyles } from "./styles";
import theme from "@/utils/theme";

import ProvidersTab from "./components/ProvidersTab/ProvidersTab";
import EncountersTab from "./components/EncountersTab/EncountersTab";
import organizationImage from "@/public/organization_icon.svg";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

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
    dispatch(fetchOrganizationEncounters(id));
  }, [id, dispatch]);

  if (loading) {
    return <div className={classes.pageLoading}>Loading facility data...</div>;
  }
  if (error || !organization) {
    return (
      <div className={classes.pageError}>{error ?? "Facility not found."}</div>
    );
  }

  return (
    <div className={classes.pageContainer}>
      <div className={classes.identityCard}>
        <div className={classes.imageBlock}>
          <img
            src={organizationImage.src}
            alt="Organization Icon"
            className={classes.avatarImage}
          />
        </div>
        <div className={classes.nameBlock}>
          <p className={classes.profileLabel}>Facility Profile</p>
          <h1 className={classes.orgFullName}>{organization.name ?? "Unknown"}</h1>
          <div className={classes.badgesRow}>
            {organization.city && <span className={classes.badge}>{organization.city}</span>}
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
          <Tab label="Clinicians" disableRipple />
          <Tab label="Visits" disableRipple />
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
              loading={encloading}
              onPatientClick={(pid) => router.push(`/patients/${pid}`)}
              onProviderClick={(pid) => router.push(`/providers/${pid}`)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
