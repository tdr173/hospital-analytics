"use client";

import useClasses from "@/utils/useClasses";
import { EncounterMedicationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { MedicationsTabStyles } from "./MedicationsTabStyles";

const COLS = "2fr 1fr 100px 100px 80px 1.5fr";

interface Props {
  data: EncounterMedicationItem[];
}

export default function MedicationsTab({ data }: Props) {
  const classes = useClasses(MedicationsTabStyles, { name: "MedicationsTab" });
  if (!data.length) {
    return <div className={classes.emptyState}>No medications recorded.</div>;
  }
  return (
    <>
      <div
        className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: COLS }}
      >
        <div>Description</div>
        <div>Code</div>
        <div>Started</div>
        <div>Ended</div>
        <div>Duration</div>
        <div>Reason</div>
      </div>
      {data.map((r, i) => (
        <div
          key={r.id}
          className={`${classes.gridRow} ${classes.dataRow} ${
            i % 2 === 0 ? classes.rowEven : classes.rowOdd
          }`}
          style={{ gridTemplateColumns: COLS }}
        >
          <div className={classes.cellPrimary}>{r.description}</div>
          <div className={classes.cellCode}>{r.medicationCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>
            {r.endDate ? formatDate(r.endDate) : "-"}
          </div>
          <div className={classes.cellSecondary}>
            {r.durationDays != null ? `${Math.round(r.durationDays)}d` : "-"}
          </div>
          <div className={classes.cellSecondary}>
            {r.reasonDescription ?? "-"}
          </div>
        </div>
      ))}
    </>
  );
}
