"use client";

import { CarePlanItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import carePlansTabStyles from "./CarePlansTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

export default function CarePlansTab({ data }: { data: CarePlanItem[] }) {
  const classes = useClasses(carePlansTabStyles, {
    name: "CarePlansTabStyles",
  });

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No care plans recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`}>
          <div>Care Plan</div>
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
              <TruncatedText text={r.description} />

              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
              </div>

              <div className={classes.centeredCell}>
                {r.endDate ? formatDate(r.endDate) : "-"}
              </div>

              <div className={classes.centeredCell}>
                {r.durationDays != null
                  ? `${Math.round(r.durationDays)} d`
                  : "-"}
              </div>

              <div className={classes.secondaryText}>
                {r.reasonDescription ? (
                  <TruncatedText text={r.reasonDescription} />
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
