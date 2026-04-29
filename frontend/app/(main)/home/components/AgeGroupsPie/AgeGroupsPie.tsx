"use client";

import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import { AgeGroupItem } from "@/models/generic/dashboard";
import { AgeGroupsPieStyles } from "./AgeGroupsPieStyles";

const AGE_GROUP_COLORS = theme.colors.charts.ageGroups;

interface Props {
  data: AgeGroupItem[];
}

export default function AgeGroupsPie({ data }: Props) {
  const classes = useClasses(AgeGroupsPieStyles, { name: "AgeGroupsPie" });

  const pieData = data.map((d) => ({
    name: d.ageGroup,
    value: d.count,
    tooltip: `${d.ageGroup}: ${d.count.toLocaleString()}`,
  }));

  return (
    <div className={classes.card}>
      <p className={classes.title}>Age Groups</p>
      {pieData.length === 0 ? (
        <div className={classes.empty}>No patient data available.</div>
      ) : (
        <PieChartComponent data={pieData} title="" colors={AGE_GROUP_COLORS} />
      )}
    </div>
  );
}
