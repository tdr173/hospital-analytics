"use client";

import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import useClasses from "@/utils/useClasses";
import { formatDate } from "@/utils/functions";
import { RecentEncounterItem } from "@/models/generic/dashboard";
import { RecentEncountersTableStyles } from "./RecentEncountersTableStyles";
import EncounterTag from "@/components/generic_components/EncounterTag/EncounterTag";

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
      <p className={classes.title}>Recent Visits</p>
      <div className={`${classes.grid} ${classes.header}`}>
        <div>Patient</div>
        <div>Doctor</div>
        <div>Facility</div>
        <div>Date</div>
        <div>Type</div>
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
          <div className={classes.secondary}>{r.organizationName ?? "-"}</div>
          <div className={classes.secondary}>{formatDate(r.startDate)}</div>
          <div>
            <EncounterTag type={r.encounterClass} />
          </div>
          <div className={classes.secondary}>{r.description}</div>
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
    </div>
  );
}
