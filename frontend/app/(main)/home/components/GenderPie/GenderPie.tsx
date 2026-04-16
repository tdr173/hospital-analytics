"use client";

import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import { GenderDistributionItem } from "@/models/generic/dashboard";
import { GenderPieStyles } from "./GenderPieStyles";

const GENDER_COLORS: Record<string, string> = {
  M: theme.colors.gender.male,
  F: theme.colors.gender.female,
};

interface Props {
  data: GenderDistributionItem[];
}

export default function GenderPie({ data }: Props) {
  const classes = useClasses(GenderPieStyles, { name: "GenderPie" });

  const pieData = data.map((d) => {
    const name = d.gender === "M" ? "Male" : d.gender === "F" ? "Female" : d.gender;
    return {
      name,
      value: d.count,
      tooltip: `${name}: ${d.count.toLocaleString()}`,
    };
  });
  const colors = data.map(
    (d) => GENDER_COLORS[d.gender] ?? theme.colors.primary.main,
  );

  return (
    <div className={classes.card}>
      <p className={classes.title}>Gender</p>
      {pieData.length === 0 ? (
        <div className={classes.empty}>No patient data available.</div>
      ) : (
        <PieChartComponent data={pieData} title="" colors={colors} />
      )}
    </div>
  );
}
