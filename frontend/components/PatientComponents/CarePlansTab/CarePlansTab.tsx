"use client";

import { CarePlanItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import carePlansTabStyles from "./CarePlansTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface CarePlansTabProps {
  data: CarePlanItem[];
  onEdit?: (item: CarePlanItem) => void;
  onDelete?: (item: CarePlanItem) => void;
}

export default function CarePlansTab({ data, onEdit, onDelete }: CarePlansTabProps) {
  const classes = useClasses(carePlansTabStyles, {
    name: "CarePlansTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  const gridTemplate = showActions
    ? "2fr 1fr 1fr 1fr 1fr 80px"
    : "2fr 1fr 1fr 1fr 1fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No care plans recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`} style={{ gridTemplateColumns: gridTemplate }}>
          <div>Care Plan</div>
          <div>Start Date</div>
          <div>End Date</div>
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
