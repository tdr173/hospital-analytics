"use client";

import { EncounterItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import encountersTabStyles from "./EncountersTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import RowActions from "@/components/generic_components/RowActions/RowActions";
import EncounterTag from "@/components/generic_components/EncounterTag/EncounterTag";

interface EncountersTabProps {
  data: EncounterItem[];
  onEdit?: (item: EncounterItem) => void;
  onDelete?: (item: EncounterItem) => void;
}

export default function EncountersTab({ data, onEdit, onDelete }: EncountersTabProps) {
  const classes = useClasses(encountersTabStyles, {
    name: "EncountersTabStyles",
  });
  const showActions = !!(onEdit || onDelete);
  const gridTemplate = showActions
    ? "0.7fr 1.5fr 2.5fr 1.5fr 2fr 0.5fr 80px"
    : "0.7fr 1.5fr 2.5fr 1.5fr 2fr 0.5fr";

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        {!data || data.length === 0 ? (
          <div className={classes.emptyState}>No visits recorded.</div>
        ) : (
          <>
            <div className={`${classes.gridRow} ${classes.headerRow}`} style={{ gridTemplateColumns: gridTemplate }}>
              <div>Date</div>
              <div>Type</div>
              <div>Description</div>
              <div>Doctor</div>
              <div>Facility</div>
              <div>Duration</div>
              {showActions && <div>Actions</div>}
            </div>

            {data.map((r, index) => {
              const rowColorClass =
                index % 2 === 0 ? classes.rowEven : classes.rowOdd;

              return (
                <div
                  key={r.encounterId}
                  className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
                  style={{ gridTemplateColumns: gridTemplate }}
                >
                  <div className={classes.centeredCell}>
                    {formatDate(r.startDate)}
                  </div>

                  <div className={classes.centeredCell}>
                    <EncounterTag type={r.encounterClass} />
                  </div>

                  <div className={classes.truncatedCell}>
                    <TruncatedText text={r.description} />
                  </div>

                  <div className={classes.secondaryText}>
                    <TruncatedText text={r.providerName ?? "-"} />
                  </div>

                  <div className={classes.secondaryText}>
                    <TruncatedText text={r.organizationName ?? "-"} />
                  </div>

                  <div className={classes.centeredCell}>
                    {r.duration != null ? `${Math.round(r.duration)} min` : "-"}
                  </div>

                  {showActions && (
                    <RowActions item={r} onEdit={onEdit} onDelete={onDelete} />
                  )}
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
