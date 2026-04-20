"use client";

import useClasses from "@/utils/useClasses";
import { OrganizationEncounterItem } from "@/models/generic/organizations";
import { formatDate } from "@/utils/functions";
import { EncountersTabStyles } from "./EncountersTabStyles";

const ENCOUNTER_CLASS_LABELS: Record<string, string> = {
  inpatient: "Inpatient",
  ambulatory: "Ambulatory",
  wellness: "Wellness",
  emergency: "Emergency",
  urgentcare: "Urgent Care",
};

interface Props {
  data: OrganizationEncounterItem[];
  loading: boolean;
  onPatientClick: (id: string) => void;
  onProviderClick: (id: string) => void;
}

export default function EncountersTab({
  data,
  loading,
  onPatientClick,
  onProviderClick,
}: Props) {
  const classes = useClasses(EncountersTabStyles, { name: "OrgEncountersTab" });

  if (loading)
    return <div className={classes.tabLoading}>Loading visits...</div>;
  if (!data.length)
    return <div className={classes.emptyState}>No visits recorded.</div>;

  return (
    <div className={classes.container}>
      <div className={classes.scroller}>
        <div
          className={`${classes.gridRow} ${classes.encountersGridRow} ${classes.headerRow}`}
        >
          <div>Patient</div>
          <div>Doctor</div>
          <div>Date</div>
          <div>Type</div>
          <div>Description</div>
          <div>Duration</div>
        </div>
        {data.map((r, i) => (
          <div
            key={r.encounterId}
            className={`${classes.gridRow} ${classes.encountersGridRow} ${classes.dataRow} ${
              i % 2 === 0 ? classes.rowEven : classes.rowOdd
            }`}
          >
            <div
              className={classes.clickableCell}
              onClick={() => onPatientClick(r.patientId)}
            >
              {r.patientName}
            </div>
            <div
              className={classes.clickableCell}
              onClick={() => onProviderClick(r.providerId)}
            >
              {r.providerName}
            </div>
            <div className={classes.secondaryText}>
              {formatDate(r.startDate)}
            </div>
            <div>
              <span className={classes.classBadge}>
                {ENCOUNTER_CLASS_LABELS[r.encounterClass] ?? r.encounterClass}
              </span>
            </div>
            <div className={classes.secondaryText}>{r.description}</div>
            <div className={classes.secondaryText}>
              {r.duration != null ? `${Math.round(r.duration)} min` : "-"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
