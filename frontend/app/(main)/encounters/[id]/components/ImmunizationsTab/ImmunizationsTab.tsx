"use client";

import { EncounterImmunizationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import immunizationsTabStyles from "./ImmunizationsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface ImmunizationsTabProps {
  data: EncounterImmunizationItem[];
  onEdit?: (item: EncounterImmunizationItem) => void;
  onDelete?: (item: EncounterImmunizationItem) => void;
}

export default function ImmunizationsTab({
  data,
  onEdit,
  onDelete,
}: ImmunizationsTabProps) {
  const classes = useClasses(immunizationsTabStyles, {
    name: "ImmunizationsTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  // Using 3fr for description, 1fr for code, and 1fr for date
  const gridTemplate = showActions ? "3fr 1fr 1fr 80px" : "3fr 1fr 1fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No immunizations recorded.</div>;
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
          <div>Date</div>
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

              <div className={classes.immunizationCode}>
                {r.immunizationCode}
              </div>

              <div className={classes.centeredCell}>{formatDate(r.date)}</div>

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
