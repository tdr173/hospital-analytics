"use client";

import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import { EncounterClassItem } from "@/models/generic/dashboard";
import { LastWeekClassPieStyles } from "./LastWeekClassPieStyles";
import { capitalize } from "../../utils/formatters";

const ENCOUNTER_CLASS_COLORS: Record<string, string> = {
  emergency: "#ef4444",
  ambulatory: theme.colors.primary.main,
  inpatient: "#8b5cf6",
  wellness: "#10b981",
  urgentcare: "#f59e0b",
};

interface Props {
  data: EncounterClassItem[];
}

export default function LastWeekClassPie({ data }: Props) {
  const classes = useClasses(LastWeekClassPieStyles, {
    name: "LastWeekClassPie",
  });

  const pieData = data.map((d) => ({
    name: capitalize(d.encounterClass),
    value: d.count,
    tooltip: `${capitalize(d.encounterClass)}: ${d.count.toLocaleString()}`,
  }));
  const colors = data.map(
    (d) =>
      ENCOUNTER_CLASS_COLORS[d.encounterClass] ?? theme.colors.secondary.main,
  );

  return (
    <div className={classes.card}>
      <p className={classes.title}>Last Week – Visits by Type</p>
      {pieData.length === 0 ? (
        <div className={classes.empty}>No visits recorded in the last week.</div>
      ) : (
        <PieChartComponent data={pieData} title="" colors={colors} />
      )}
    </div>
  );
}
