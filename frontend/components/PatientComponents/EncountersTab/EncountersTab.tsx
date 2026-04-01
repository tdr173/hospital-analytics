"use client";

import { EncounterItem } from "@/models/generic/patients";
import { formatDate } from "@/utils/functions";
import useClasses from "@/utils/useClasses";
import encountersTabStyles from "./EncountersTabStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

const ENCOUNTER_CLASS_LABELS: Record<string, string> = {
  inpatient: "Inpatient",
  ambulatory: "Ambulatory",
  wellness: "Wellness",
  emergency: "Emergency",
  urgentcare: "Urgent Care",
};

export default function EncountersTab({ data }: { data: EncounterItem[] }) {
  const classes = useClasses(encountersTabStyles, {
    name: "EncountersTabStyles",
  });

  return (
    <div className={classes.tableContainer}>
      <div className={classes.scrollWrapper}>
        {!data || data.length === 0 ? (
          <div className={classes.emptyState}>No encounters recorded.</div>
        ) : (
          <>
            <div className={`${classes.gridRow} ${classes.headerRow}`}>
              <div>Date</div>
              <div>Type</div>
              <div>Description</div>
              <div>Provider</div>
              <div>Organization</div>
              <div>Duration</div>
            </div>

            {data.map((r, index) => {
              const rowColorClass =
                index % 2 === 0 ? classes.rowEven : classes.rowOdd;
              const typeLabel =
                ENCOUNTER_CLASS_LABELS[r.encounter_class] ?? r.encounter_class;

              return (
                <div
                  key={r.encounter_id}
                  className={`${classes.gridRow} ${classes.dataRow} ${rowColorClass}`}
                >
                  {/* Col 1: Centered Date */}
                  <div className={classes.centeredCell}>
                    {formatDate(r.start_date)}
                  </div>

                  {/* Col 2: Centered Type Badge */}
                  <div className={classes.centeredCell}>
                    <span className={classes.encounterTypeBadge}>
                      {typeLabel}
                    </span>
                  </div>

                  {/* Col 3: Description (Truncated) */}
                  <div className={classes.truncatedCell}>
                    <TruncatedText text={r.description} />
                  </div>

                  {/* Col 4: Provider (Truncated) */}
                  <div className={classes.secondaryText}>
                    <TruncatedText text={r.provider_name ?? "—"} />
                  </div>

                  {/* Col 5: Organization (Truncated) */}
                  <div className={classes.secondaryText}>
                    <TruncatedText text={r.organization_name ?? "—"} />
                  </div>

                  {/* Col 6: Centered Duration */}
                  <div className={classes.centeredCell}>
                    {r.duration != null ? `${Math.round(r.duration)} min` : "—"}
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
