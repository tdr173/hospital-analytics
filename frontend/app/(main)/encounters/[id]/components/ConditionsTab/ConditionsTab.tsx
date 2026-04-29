"use client";

import { EncounterConditionItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import conditionsTabStyles from "./ConditionsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface ConditionsTabProps {
  data: EncounterConditionItem[];
  onEdit?: (item: EncounterConditionItem) => void;
  onDelete?: (item: EncounterConditionItem) => void;
}

export default function ConditionsTab({
  data,
  onEdit,
  onDelete,
}: ConditionsTabProps) {
  const classes = useClasses(conditionsTabStyles, {
    name: "ConditionsTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  const gridTemplate = showActions ? "3fr 1fr 1fr 1fr 80px" : "3fr 1fr 1fr 1fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No conditions recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div
          className={`${classes.gridRow} ${classes.headerRow}`}
          style={{ gridTemplateColumns: gridTemplate }}
        >
          <div>Description</div>
          <div>Code</div>
          <div>Started</div>
          <div>Status</div>
          {showActions && <div>Actions</div>}
        </div>

        {data.map((r, index) => {
          const rowColorClass =
            index % 2 === 0 ? classes.rowEven : classes.rowOdd;

          return (
            <div
              key={r.id}
              className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
              style={{ gridTemplateColumns: gridTemplate }}
            >
              <TruncatedText text={r.description} />

              <div className={classes.conditionCode}>{r.conditionCode}</div>

              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
              </div>

              <div className={classes.centeredCell}>
                {r.endDate ? (
                  <span className={classes.badgeResolved}>Resolved</span>
                ) : (
                  <span className={classes.badgeActive}>Active</span>
                )}
              </div>

              {showActions && (
                <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
