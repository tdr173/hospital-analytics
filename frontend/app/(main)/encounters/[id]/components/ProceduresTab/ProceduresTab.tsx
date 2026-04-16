"use client";

import useClasses from "@/utils/useClasses";
import { EncounterProcedureItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { ProceduresTabStyles } from "./ProceduresTabStyles";

const COLS = "2.5fr 1fr 110px 2fr";

interface Props {
  data: EncounterProcedureItem[];
}

export default function ProceduresTab({ data }: Props) {
  const classes = useClasses(ProceduresTabStyles, { name: "ProceduresTab" });
  if (!data.length) {
    return <div className={classes.emptyState}>No procedures recorded.</div>;
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
          <div className={classes.cellCode}>{r.procedureCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>{r.reasonDescription ?? "—"}</div>
        </div>
      ))}
    </>
  );
}
