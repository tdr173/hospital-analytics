"use client";

import { MedicationItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import medicationsTabStyles from "./MedicationsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

export default function MedicationsTab({ data }: { data: MedicationItem[] }) {
  const classes = useClasses(medicationsTabStyles, {
    name: "MedicationsTabStyles",
  });

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No medications recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`}>
          <div>Medication</div>
          <div>Start Date</div>
          <div>End Date</div>
          <div>Duration</div>
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
              {/* Column 1: Left Aligned */}
              <TruncatedText text={r.description} />

              {/* Column 2: Centered Start Date */}
              <div className={classes.centeredCell}>
                {formatDate(r.start_date)}
              </div>

              {/* Column 3: Centered End Date */}
              <div className={classes.centeredCell}>
                {r.end_date ? formatDate(r.end_date) : "—"}
              </div>

              {/* Column 4: Centered Duration */}
              <div className={classes.centeredCell}>
                {r.duration_days != null
                  ? `${Math.round(r.duration_days)} d`
                  : "—"}
              </div>

              {/* Column 5: Centered Reason */}
              <div className={classes.secondaryText}>
                {r.reason_description ? (
                  <TruncatedText text={r.reason_description} />
                ) : (
                  "-"
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
