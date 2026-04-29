"use client";

import useClasses from "@/utils/useClasses";
import { EncounterObservationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import { ObservationsTabStyles } from "./ObservationsTabStyles";
import RowActions from "@/components/generic_components/RowActions/RowActions";

const BASE_COLS = "2fr 1.5fr 80px 110px";

interface Props {
  data: EncounterObservationItem[];
  onEdit?: (item: EncounterObservationItem) => void;
  onDelete?: (item: EncounterObservationItem) => void;
}

export default function ObservationsTab({ data, onEdit, onDelete }: Props) {
  const classes = useClasses(ObservationsTabStyles, {
    name: "ObservationsTab",
  });
  const showActions = !!(onEdit || onDelete);
  const COLS = showActions ? `${BASE_COLS} 80px` : BASE_COLS;

  if (!data.length) {
    return <div className={classes.emptyState}>No test results recorded.</div>;
  }

  const maxNumeric = Math.max(...data.map((d) => d.valueNumeric ?? 0), 1);

  return (
    <>
      <div
        className={`${classes.gridRow} ${classes.headerRow}`}
        style={{ gridTemplateColumns: COLS }}
      >
        <div>Description</div>
        <div>Value</div>
        <div>Units</div>
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
          <div className={classes.obsValueRow}>
            {r.valueNumeric != null ? (
              <>
                <div
                  className={classes.obsBar}
                  style={{
                    width: `${Math.max(4, (r.valueNumeric / maxNumeric) * 80)}px`,
                  }}
                />
                <span className={classes.cellNumeric}>{r.valueNumeric}</span>
              </>
            ) : (
              <span className={classes.cellSecondary}>{r.value}</span>
            )}
          </div>
          <div className={classes.cellSecondary}>{r.units ?? "-"}</div>
          <div className={classes.cellSecondary}>{formatDate(r.date)}</div>
          {showActions && <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />}
        </div>
      ))}
    </>
  );
}
