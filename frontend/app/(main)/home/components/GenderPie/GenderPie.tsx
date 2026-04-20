"use client";

import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import { GenderDistributionItem } from "@/models/generic/dashboard";
import { GenderPieStyles } from "./GenderPieStyles";

const GENDER_COLORS: Record<string, string> = {
  M: theme.colors.charts.gender.male,
  F: theme.colors.charts.gender.female,
};

interface Props {
  data: GenderDistributionItem[];
}

export default function GenderPie({ data }: Props) {
  const classes = useClasses(GenderPieStyles, { name: "GenderPie" });

  const barData = data.map((d) => {
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
      {barData.length === 0 ? (
        <div className={classes.empty}>No patient data available.</div>
      ) : (
        <BarChartComponent data={barData} title="" colors={colors} />
      )}
    </div>
  );
}
