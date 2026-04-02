"use client";

import { AllergyItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import allergiesTabStyles from "./AllergiesTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

export default function AllergiesTab({ data }: { data: AllergyItem[] }) {
  const classes = useClasses(allergiesTabStyles, {
    name: "AllergiesTabStyles",
  });

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No allergies recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`}>
          <div>Allergen</div>
          <div>Recorded</div>
          <div>Status</div>
        </div>

        {data.map((r, index) => {
          const rowColorClass =
            index % 2 === 0 ? classes.rowEven : classes.rowOdd;

          return (
            <div
              key={r.id}
              className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
            >
              {/* Column 1: Allergen Name */}
              <TruncatedText text={r.description} />

              {/* Column 2: Centered Recorded Date */}
              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
              </div>

              {/* Column 3: Centered Status */}
              <div className={classes.centeredCell}>
                {r.endDate ? (
                  <span className={classes.allergyResolved}>
                    Resolved {formatDate(r.endDate)}
                  </span>
                ) : (
                  <span className={classes.allergyActive}>Active</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
