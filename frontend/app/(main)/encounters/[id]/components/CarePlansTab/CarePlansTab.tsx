"use client";

import useClasses from "@/utils/useClasses";
import { EncounterCarePlanItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { CarePlansTabStyles } from "./CarePlansTabStyles";

const COLS = "2.5fr 1fr 110px 2fr";

interface Props {
  data: EncounterCarePlanItem[];
}

export default function CarePlansTab({ data }: Props) {
  const classes = useClasses(CarePlansTabStyles, { name: "CarePlansTab" });
  if (!data.length) {
    return <div className={classes.emptyState}>No care plans recorded.</div>;
  }
  return (
    <>
      <div
        className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: COLS }}
      >
        <div>Description</div>
        <div>Code</div>
        <div>Date</div>
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
          <div className={classes.cellCode}>{r.careplanCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>{r.reasonDescription ?? "—"}</div>
        </div>
      ))}
    </>
  );
}
