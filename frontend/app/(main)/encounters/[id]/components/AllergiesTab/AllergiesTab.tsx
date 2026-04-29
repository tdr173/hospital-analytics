"use client";

import useClasses from "@/utils/useClasses";
import { EncounterAllergyItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { AllergiesTabStyles } from "./AllergiesTabStyles";
import RowActions from "@/components/generic_components/RowActions/RowActions";

const BASE_COLS = "3fr 1fr 110px 80px";

interface Props {
  data: EncounterAllergyItem[];
  onEdit?: (item: EncounterAllergyItem) => void;
  onDelete?: (item: EncounterAllergyItem) => void;
}

export default function AllergiesTab({ data, onEdit, onDelete }: Props) {
  const classes = useClasses(AllergiesTabStyles, { name: "AllergiesTab" });
  const showActions = !!(onEdit || onDelete);
  const COLS = showActions ? `${BASE_COLS} 80px` : BASE_COLS;

  if (!data.length) {
    return <div className={classes.emptyState}>No allergies recorded.</div>;
  }
  return (
    <>
      <div
        className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: COLS }}
      >
        <div>Description</div>
        <div>Code</div>
        <div>Recorded</div>
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
          <div className={classes.cellCode}>{r.allergyCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div>
            {r.endDate ? (
              <span className={classes.badgeResolved}>Resolved</span>
            ) : (
              <span className={classes.badgeWarning}>Active</span>
            )}
          </div>
          {showActions && <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />}
        </div>
      ))}
    </>
  );
}
