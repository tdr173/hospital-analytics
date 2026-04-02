"use client";

import { ConditionItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import conditionsTabStyles from "./ConditionsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

export default function ConditionsTab({ data }: { data: ConditionItem[] }) {
  const classes = useClasses(conditionsTabStyles, {
    name: "ConditionsTabStyles",
  });

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No conditions recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`}>
          <div>Condition</div>
          <div>Condition Code</div>
          <div>Start Date</div>
          <div>End Date</div>
        </div>

        {data.map((r, index) => {
          const rowColorClass =
            index % 2 === 0 ? classes.rowEven : classes.rowOdd;

          return (
            <div
              key={r.id}
              className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
            >
              {/* Column 1: Left Aligned (Default) */}
              {<TruncatedText text={r.description} />}

              {/* Column 2: Centered Code */}
              <div className={classes.snomedCode}>{r.conditionCode}</div>

              {/* Column 3: Centered Start Date */}
              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
              </div>

              {/* Column 4: Centered End Date/Badge */}
              <div className={classes.centeredCell}>
                {r.endDate ? (
                  formatDate(r.endDate)
                ) : (
                  <span className={classes.ongoingBadge}>Ongoing</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
