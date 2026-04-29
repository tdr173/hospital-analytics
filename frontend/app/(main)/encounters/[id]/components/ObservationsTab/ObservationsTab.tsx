"use client";

import { EncounterObservationItem } from "@/models/generic/encounters";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import observationsTabStyles from "./ObservationsTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";

interface ObservationsTabProps {
  data: EncounterObservationItem[];
  onEdit?: (item: EncounterObservationItem) => void;
  onDelete?: (item: EncounterObservationItem) => void;
}

export default function ObservationsTab({
  data,
  onEdit,
  onDelete,
}: ObservationsTabProps) {
  const classes = useClasses(observationsTabStyles, {
    name: "ObservationsTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  // Using 3fr for description, 2fr for the value/bar, and 1fr for units/date
  const gridTemplate = showActions ? "3fr 2fr 1fr 1fr 80px" : "3fr 2fr 1fr 1fr";

  if (!data || data.length === 0) {
    return <div className={classes.emptyState}>No test results recorded.</div>;
  }

  // Calculate max to scale the bars properly
  const maxNumeric = Math.max(...data.map((d) => d.valueNumeric ?? 0), 1);

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        <div
          className={`${classes.gridRow} ${classes.headerRow}`}
          style={{ gridTemplateColumns: gridTemplate }}
        >
          <div>Description</div>
          <div className={classes.alignLeft}>Value</div>
          <div>Units</div>
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

              <div className={classes.obsValueRow}>
                {r.valueNumeric != null ? (
                  <>
                    <div
                      className={classes.obsBar}
                      style={{
                        width: `${Math.max(4, (r.valueNumeric / maxNumeric) * 80)}px`,
                      }}
                    />
                    <span className={classes.cellNumeric}>
                      {r.valueNumeric}
                    </span>
                  </>
                ) : (
                  <span className={classes.cellSecondary}>
                    {<TruncatedText text={r.value || "-"} />}
                  </span>
                )}
              </div>

              <div className={classes.centeredCell}>{r.units ?? "-"}</div>

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
