"use client";

import useClasses from "@/utils/useClasses";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import { ClusterDistributionItem } from "@/models/generic/dashboard";
import { ClusterDistributionCardStyles } from "./ClusterDistributionCardStyles";

interface Props {
  data: ClusterDistributionItem[];
}

export default function ClusterDistributionCard({ data }: Props) {
  const classes = useClasses(ClusterDistributionCardStyles, {
    name: "ClusterDistributionCard",
  });

  if (data.length === 0) {
    return (
      <div className={classes.card}>
        <p className={classes.title}>Patient Group Distribution</p>
        <div className={classes.empty}>
          No patient groups yet. Run the grouping analysis first.
        </div>
      </div>
    );
  }

  const pieData = data.map((d) => ({
    name: d.title,
    value: d.count,
    tooltip: `${d.title}: ${d.count.toLocaleString()}`,
  }));
  const colors = data.map((d) => d.color);

  return (
    <div className={classes.card}>
      <p className={classes.title}>Patient Group Distribution</p>
      <PieChartComponent data={pieData} title="" colors={colors} />
    </div>
  );
}
