"use client";

import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import useClasses from "@/utils/useClasses";
import { formatDate } from "@/utils/functions";
import { RecentEncounterItem } from "@/models/generic/dashboard";
import { RecentEncountersTableStyles } from "./RecentEncountersTableStyles";

interface Props {
  data: RecentEncounterItem[];
  onPatientClick: (id: string) => void;
  onEncounterClick: (id: string) => void;
}

export default function RecentEncountersTable({
  data,
  onPatientClick,
  onEncounterClick,
}: Props) {
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
        <div className={classes.actionsHeader}>Actions</div>
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
          <div className={classes.actionsCell}>
            <IconButton
              size="small"
              className={classes.actionButton}
              onClick={() => onEncounterClick(r.encounterId)}
              aria-label="View encounter"
            >
              <VisibilityOutlinedIcon sx={{ fontSize: "1.05rem" }} />
            </IconButton>
          </div>
        </div>
      ))}
    </div>
  );
}
