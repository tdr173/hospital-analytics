"use client";

import useClasses from "@/utils/useClasses";
import { EncounterConditionItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { ConditionsTabStyles } from "./ConditionsTabStyles";
import RowActions from "@/components/generic_components/RowActions/RowActions";

const BASE_COLS = "2.5fr 1fr 110px 80px";

interface Props {
  data: EncounterConditionItem[];
  onEdit?: (item: EncounterConditionItem) => void;
  onDelete?: (item: EncounterConditionItem) => void;
}

export default function ConditionsTab({ data, onEdit, onDelete }: Props) {
  const classes = useClasses(ConditionsTabStyles, { name: "ConditionsTab" });
  const showActions = !!(onEdit || onDelete);
  const COLS = showActions ? `${BASE_COLS} 80px` : BASE_COLS;

  if (!data.length) {
    return <div className={classes.emptyState}>No conditions recorded.</div>;
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
        <div>Status</div>
        {showActions && <div>Actions</div>}
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
          <div className={classes.cellCode}>{r.conditionCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div>
            {r.endDate ? (
              <span className={classes.badgeResolved}>Resolved</span>
            ) : (
              <span className={classes.badgeActive}>Active</span>
            )}
          </div>
          {showActions && <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />}
        </div>
      ))}
    </>
  );
}
