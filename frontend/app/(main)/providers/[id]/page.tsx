"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";

import { RootState, AppDispatch } from "@/store";
import {
  fetchProviderDetail,
  fetchProviderEncounters,
} from "@/store/slices/providers/thunks";
import { resetCurrentProvider } from "@/store/slices/providers/current-provider-slice";
import { ProviderEncounterItem } from "@/models/generic/providers";

import useClasses from "@/utils/useClasses";
import { ProviderDetailPageStyles } from "./styles";
import { clearName, formatDate } from "@/utils/functions";
import manImage from "@/public/man_icon.svg";
import womanImage from "@/public/woman_icon.svg";
import EncounterTag from "@/components/generic_components/EncounterTag/EncounterTag";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const GENDER_LABELS: Record<string, string> = {
  M: "Male",
  F: "Female",
};

function EncountersTable({
  data,
  encloading,
  encLoadingMore,
  encHasMore,
  classes,
  onPatientClick,
  onEncounterClick,
  onLoadMore,
}: {
  data: ProviderEncounterItem[];
  encloading: boolean;
  encLoadingMore: boolean;
  encHasMore: boolean;
  classes: any;
  onPatientClick: (id: string) => void;
  onEncounterClick: (id: string) => void;
  onLoadMore: () => void;
}) {
  if (encloading) {
    return (
      <div className={classes.encountersLoading}>Loading visits...</div>
    );
  }
  if (!data.length) {
    return <div className={classes.emptyState}>No visits recorded.</div>;
  }
  return (
    <>
      <div className={`${classes.gridRow} ${classes.headerRow}`}>
        <div>Patient Name</div>
        <div>Date</div>
        <div>Type</div>
        <div>Description</div>
        <div>Reason</div>
        <div>Duration</div>
        <div className={classes.actionsHeader}>Actions</div>
      </div>
      {data.map((r, index) => (
        <div
          key={r.encounterId}
          className={`${classes.gridRow} ${classes.dataRow} ${index % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
        >
          <div
            className={classes.patientLink}
            onClick={() => onPatientClick(r.patientId)}
          >
            {r.patientName}
          </div>
          <div className={classes.secondaryText}>{formatDate(r.startDate)}</div>
          <div>
            <EncounterTag type={r.encounterClass} />
          </div>
          <div className={classes.secondaryText}>{r.description}</div>
          <div className={classes.secondaryText}>
            {r.reasonDescription ?? "-"}
          </div>
          <div className={classes.secondaryText}>
            {r.duration != null ? `${Math.round(r.duration)} min` : "-"}
          </div>
          <div className={classes.actionsCell}>
            <IconButton
              size="small"
              className={classes.actionButton}
              onClick={() => onEncounterClick(r.encounterId)}
              aria-label="View visit"
            >
              <VisibilityOutlinedIcon sx={{ fontSize: "1.05rem" }} />
            </IconButton>
          </div>
        </div>
      ))}
      {encHasMore && (
        <div className={classes.loadMoreRow}>
          <button
            className={classes.loadMoreButton}
            onClick={onLoadMore}
            disabled={encLoadingMore}
          >
            {encLoadingMore ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </>
  );
}

export default function ProviderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(ProviderDetailPageStyles, {
    name: "ProviderDetailPage",
  });

  const { provider, encounters, loading, encloading, encLoadingMore, encHasMore, encPage, error } = useSelector(
    (state: RootState) => state.currentProvider,
  );

  useEffect(() => {
    if (!id) return;
    dispatch(resetCurrentProvider());
    dispatch(fetchProviderDetail(id));
    dispatch(fetchProviderEncounters({ providerId: id, page: 1 }));
  }, [id, dispatch]);

  if (loading) {
    return <div className={classes.pageLoading}>Loading doctor profile...</div>;
  }

  if (error || !provider) {
    return (
      <div className={classes.pageError}>{error ?? "Doctor not found."}</div>
    );
  }

  const details = [
    { label: "Facility", value: provider.organizationName },
    { label: "Visits", value: String(provider.encounters) },
    { label: "City", value: provider.city },
  ];

  return (
    <div className={classes.pageContainer}>
      <div className={classes.identityCard}>
        <div className={classes.imageBlock}>
          <img
            src={provider.gender === "M" ? manImage.src : womanImage.src}
            alt={provider.gender === "M" ? "Man Icon" : "Woman Icon"}
            className={classes.avatarImage}
          />
        </div>
        <div className={classes.nameBlock}>
          <p className={classes.profileLabel}>Doctor Profile</p>
          <h1 className={classes.providerFullName}>
            {clearName(provider.firstName, provider.lastName) || "Unknown Name"}
          </h1>
          <div className={classes.badgesRow}>
            {provider.speciality && (
              <span className={classes.badge}>{provider.speciality}</span>
            )}
            {provider.gender && (
              <span
                className={
                  provider.gender === "F"
                    ? classes.genderBadgeFemale
                    : classes.genderBadgeMale
                }
              >
                {GENDER_LABELS[provider.gender] ?? provider.gender}
              </span>
            )}
            {provider.city && (
              <span className={classes.badge}>{provider.city}</span>
            )}
          </div>
        </div>

        <div className={classes.detailsGrid}>
          {details.map(({ label, value }) => (
            <div key={label}>
              <p className={classes.detailLabel}>{label}</p>
              <p className={classes.detailValue}>{value ?? "-"}</p>
            </div>
          ))}
        </div>
      </div>

      <div className={classes.encountersPanel}>
        <div className={classes.encountersPanelHeader}>
          Recent Visits
        </div>
        <div className={classes.encountersPanelBody}>
          <EncountersTable
            data={encounters}
            encloading={encloading}
            encLoadingMore={encLoadingMore}
            encHasMore={encHasMore}
            classes={classes}
            onPatientClick={(patientId) =>
              router.push(`/patients/${patientId}`)
            }
            onEncounterClick={(encounterId) =>
              router.push(`/encounters/${encounterId}`)
            }
            onLoadMore={() =>
              dispatch(fetchProviderEncounters({ providerId: id, page: encPage + 1 }))
            }
          />
        </div>
      </div>
    </div>
  );
}
