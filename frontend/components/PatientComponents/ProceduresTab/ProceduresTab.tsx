"use client";

import { ProcedureItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import proceduresTabStyles from "./ProceduresTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface ProceduresTabProps {
  data: ProcedureItem[];
  onEdit?: (item: ProcedureItem) => void;
  onDelete?: (item: ProcedureItem) => void;
}

export default function ProceduresTab({ data, onEdit, onDelete }: ProceduresTabProps) {
  const classes = useClasses(proceduresTabStyles, {
    name: "ProceduresTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  const gridTemplate = showActions ? "2fr 1fr 2fr 80px" : "2fr 1fr 2fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No procedures recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`} style={{ gridTemplateColumns: gridTemplate }}>
          <div>Procedure</div>
          <div>Date</div>
          <div>Reason</div>
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

              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
              </div>

              <div className={classes.secondaryText}>
                {r.reasonDescription ? (
                  <TruncatedText text={r.reasonDescription} />
                ) : (
                  "-"
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
