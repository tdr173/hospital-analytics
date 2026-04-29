"use client";

import { AllergyItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import allergiesTabStyles from "./AllergiesTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface AllergiesTabProps {
  data: AllergyItem[];
  onEdit?: (item: AllergyItem) => void;
  onDelete?: (item: AllergyItem) => void;
}

export default function AllergiesTab({ data, onEdit, onDelete }: AllergiesTabProps) {
  const classes = useClasses(allergiesTabStyles, {
    name: "AllergiesTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  const gridTemplate = showActions ? "3fr 1fr 1fr 80px" : "3fr 1fr 1fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No allergies recorded.</div>;
  }

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div className={`${classes.gridRow} ${classes.headerRow}`} style={{ gridTemplateColumns: gridTemplate }}>
          <div>Allergen</div>
          <div>Recorded</div>
          <div>Status</div>
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
                {r.endDate ? (
                  <span className={classes.allergyResolved}>
                    Resolved {formatDate(r.endDate)}
                  </span>
                ) : (
                  <span className={classes.allergyActive}>Active</span>
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
