"use client";

import { PatientObservationItem } from "@/store/slices/patients/thunks";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import observationsTabStyles from "./ObservationsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface ObservationsTabProps {
  data: PatientObservationItem[];
  onEdit?: (item: PatientObservationItem) => void;
  onDelete?: (item: PatientObservationItem) => void;
}

export default function ObservationsTab({ data, onEdit, onDelete }: ObservationsTabProps) {
  const classes = useClasses(observationsTabStyles, {
    name: "ObservationsTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  const gridTemplate = showActions ? "1fr 2fr 1fr 1fr 80px" : "1fr 2fr 1fr 1fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No observations recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`} style={{ gridTemplateColumns: gridTemplate }}>
          <div>Date</div>
          <div>Description</div>
          <div>Code</div>
          <div>Value</div>
          {showActions && <div>Actions</div>}
        </div>

        {data.map((r, i) => {
          const rowColorClass = i % 2 === 0 ? classes.rowEven : classes.rowOdd;
          return (
            <div
              key={r.id}
              className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
              style={{ gridTemplateColumns: gridTemplate }}
            >
              <div className={classes.centeredCell}>{formatDate(r.date)}</div>
              <TruncatedText text={r.description} />
              <div className={classes.snomedCode}>{r.observationCode}</div>
              <div>
                {r.value}
                {r.units ? <span className={classes.unitsText}>{r.units}</span> : null}
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
