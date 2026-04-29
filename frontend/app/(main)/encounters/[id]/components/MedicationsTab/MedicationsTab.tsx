"use client";

import { EncounterMedicationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import medicationsTabStyles from "./MedicationsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface MedicationsTabProps {
  data: EncounterMedicationItem[];
  onEdit?: (item: EncounterMedicationItem) => void;
  onDelete?: (item: EncounterMedicationItem) => void;
}

export default function MedicationsTab({
  data,
  onEdit,
  onDelete,
}: MedicationsTabProps) {
  const classes = useClasses(medicationsTabStyles, {
    name: "MedicationsTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  // Using 3fr for description, 2fr for reason, and 1fr for the smaller metadata columns
  const gridTemplate = showActions
    ? "3fr 1fr 1fr 1fr 1fr 2fr 80px"
    : "3fr 1fr 1fr 1fr 1fr 2fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No medications recorded.</div>;
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
          <div>Ended</div>
          <div>Duration</div>
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

              <div className={classes.medicationCode}>{r.medicationCode}</div>

              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
              </div>

              <div className={classes.centeredCell}>
                {r.endDate ? formatDate(r.endDate) : "-"}
              </div>

              <div className={classes.centeredCell}>
                {r.durationDays != null
                  ? `${Math.round(r.durationDays)} d`
                  : "-"}
              </div>

              <div className={classes.reasonCell}>
                {r.reasonDescription ? (
                  <TruncatedText text={r.reasonDescription} />
                ) : (
                  <span className={classes.centeredCell}>-</span>
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