"use client";

import { ImmunizationItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import immunizationsTabStyles from "./ImmunizationsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

export default function ImmunizationsTab({
  data,
}: {
  data: ImmunizationItem[];
}) {
  const classes = useClasses(immunizationsTabStyles, {
    name: "ImmunizationsTabStyles",
  });

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No immunizations recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`}>
          <div>Vaccine</div>
          <div>Date</div>
        </div>

        {data.map((r, index) => {
          const rowColorClass =
            index % 2 === 0 ? classes.rowEven : classes.rowOdd;

          return (
            <div
              key={r.id}
              className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
            >
              {/* Column 1: Vaccine Name (Left Aligned) */}
              <TruncatedText text={r.description} />

              {/* Column 2: Centered Date */}
              <div className={classes.centeredCell}>{formatDate(r.date)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
