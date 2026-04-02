"use client";

import { ProcedureItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import proceduresTabStyles from "./ProceduresTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

export default function ProceduresTab({ data }: { data: ProcedureItem[] }) {
  const classes = useClasses(proceduresTabStyles, {
    name: "ProceduresTabStyles",
  });

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No procedures recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`}>
          <div>Procedure</div>
          <div>Date</div>
          <div>Reason</div>
        </div>

        {data.map((r, index) => {
          const rowColorClass =
            index % 2 === 0 ? classes.rowEven : classes.rowOdd;

          return (
            <div
              key={r.id}
              className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
            >
              {/* Column 1: Procedure Name (Left Aligned) */}
              <TruncatedText text={r.description} />

              {/* Column 2: Centered Date */}
              <div className={classes.centeredCell}>{formatDate(r.date)}</div>

              {/* Column 3: Centered Reason (Secondary Color) */}
              <div className={classes.secondaryText}>
                {r.reasonDescription ? (
                  <TruncatedText text={r.reasonDescription} />
                ) : (
                  "—"
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
