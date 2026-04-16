"use client";

import useClasses from "@/utils/useClasses";
import { formatDate } from "@/utils/functions";
import { RecentEncounterItem } from "@/models/generic/dashboard";
import { RecentEncountersTableStyles } from "./RecentEncountersTableStyles";

interface Props {
  data: RecentEncounterItem[];
  onPatientClick: (id: string) => void;
}

export default function RecentEncountersTable({ data, onPatientClick }: Props) {
  const classes = useClasses(RecentEncountersTableStyles, {
    name: "RecentEncountersTable",
  });

  return (
    <div className={classes.card}>
      <p className={classes.title}>Recent Encounters</p>
      <div className={`${classes.grid} ${classes.header}`}>
        <div>Patient</div>
        <div>Provider</div>
        <div>Organization</div>
        <div>Date</div>
        <div>Class</div>
        <div>Description</div>
      </div>
      {data.map((r, i) => (
        <div
          key={r.encounterId}
          className={`${classes.grid} ${i % 2 === 0 ? classes.rowEven : classes.rowOdd}`}
        >
          <div
            className={classes.clickable}
            onClick={() => onPatientClick(r.patientId)}
          >
            {r.patientName}
          </div>
          <div className={classes.secondary}>{r.providerName}</div>
          <div className={classes.secondary}>{r.organizationName ?? "—"}</div>
          <div className={classes.secondary}>{formatDate(r.startDate)}</div>
          <div>
            <span className={classes.classBadge}>{r.encounterClass}</span>
          </div>
          <div className={classes.secondary}>{r.description}</div>
        </div>
      ))}
    </div>
  );
}
