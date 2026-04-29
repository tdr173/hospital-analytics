"use client";

import { EncounterCarePlanItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import carePlansTabStyles from "./CarePlansTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface CarePlansTabProps {
  data: EncounterCarePlanItem[];
  onEdit?: (item: EncounterCarePlanItem) => void;
  onDelete?: (item: EncounterCarePlanItem) => void;
}

export default function CarePlansTab({
  data,
  onEdit,
  onDelete,
}: CarePlansTabProps) {
  const classes = useClasses(carePlansTabStyles, {
    name: "CarePlansTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  // 3fr for description, 1fr for code, 1fr for date, 2fr for reason
  const gridTemplate = showActions ? "3fr 1fr 1fr 2fr 80px" : "3fr 1fr 1fr 2fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No care plans recorded.</div>;
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

              <div className={classes.careplanCode}>{r.careplanCode}</div>

              <div className={classes.centeredCell}>
                {formatDate(r.startDate)}
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
