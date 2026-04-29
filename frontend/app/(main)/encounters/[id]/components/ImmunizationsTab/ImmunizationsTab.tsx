"use client";

import useClasses from "@/utils/useClasses";
import { EncounterImmunizationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { ImmunizationsTabStyles } from "./ImmunizationsTabStyles";
import RowActions from "@/components/generic_components/RowActions/RowActions";

const BASE_COLS = "3fr 1fr 120px";

interface Props {
  data: EncounterImmunizationItem[];
  onEdit?: (item: EncounterImmunizationItem) => void;
  onDelete?: (item: EncounterImmunizationItem) => void;
}

export default function ImmunizationsTab({ data, onEdit, onDelete }: Props) {
  const classes = useClasses(ImmunizationsTabStyles, { name: "ImmunizationsTab" });
  const showActions = !!(onEdit || onDelete);
  const COLS = showActions ? `${BASE_COLS} 80px` : BASE_COLS;

  if (!data.length) {
    return <div className={classes.emptyState}>No immunizations recorded.</div>;
  }
  return (
    <>
      <div
        className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: COLS }}
      >
        <div>Description</div>
        <div>Code</div>
        <div>Date</div>
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
          <div className={classes.cellCode}>{r.immunizationCode}</div>
          <div className={classes.cellSecondary}>{formatDate(r.date)}</div>
          {showActions && <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />}
        </div>
      ))}
    </>
  );
}
