"use client";

import useClasses from "@/utils/useClasses";
import { EncounterMedicationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { MedicationsTabStyles } from "./MedicationsTabStyles";
import RowActions from "@/components/generic_components/RowActions/RowActions";

const BASE_COLS = "2fr 1fr 100px 100px 80px 1.5fr";

interface Props {
  data: EncounterMedicationItem[];
  onEdit?: (item: EncounterMedicationItem) => void;
  onDelete?: (item: EncounterMedicationItem) => void;
}

export default function MedicationsTab({ data, onEdit, onDelete }: Props) {
  const classes = useClasses(MedicationsTabStyles, { name: "MedicationsTab" });
  const showActions = !!(onEdit || onDelete);
  const COLS = showActions ? `${BASE_COLS} 80px` : BASE_COLS;

  if (!data.length) {
    return <div className={classes.emptyState}>No medications recorded.</div>;
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
        <div>Ended</div>
        <div>Duration</div>
        <div>Reason</div>
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
          <div className={classes.cellCode}>{r.medicationCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.startDate)}</div>
          <div className={classes.cellSecondary}>
            {r.endDate ? formatDate(r.endDate) : "-"}
          </div>
          <div className={classes.cellSecondary}>
            {r.durationDays != null ? `${Math.round(r.durationDays)}d` : "-"}
          </div>
          <div className={classes.cellSecondary}>
            {r.reasonDescription ?? "-"}
          </div>
          {showActions && <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />}
        </div>
      ))}
    </>
  );
}
