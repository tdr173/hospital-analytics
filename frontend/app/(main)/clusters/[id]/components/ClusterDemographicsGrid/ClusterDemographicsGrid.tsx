"use client";

import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { ClusterDemographics } from "@/models/generic/clusters";
import { ClusterDemographicsGridStyles } from "./ClusterDemographicsGridStyles";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";

interface Props {
  demographics: ClusterDemographics;
  color: string;
}

const MARITAL_LABELS: Record<string, string> = {
  M: "Married",
  S: "Single",
  D: "Divorced",
  W: "Widowed",
};

const SMOKING_LABELS: Record<string, string> = {
  current: "Current",
  former: "Former",
  never: "Never",
};

const BURDEN_LABELS: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

const BURDEN_ORDER = ["low", "medium", "high"];
const MARITAL_ORDER = ["M", "S", "D", "W"];
const SMOKING_ORDER = ["current", "former", "never"];

const BURDEN_COLORS = theme.colors.charts.burden;

function mapDistribution(
  dist: Record<string, number>,
  labels: Record<string, string>,
  order: string[],
) {
  return order.map((key) => ({
    name: labels[key] ?? key,
    value: dist[key] ?? 0,
    tooltip: `${labels[key] ?? key}: ${dist[key] ?? 0}%`,
  }));
}

export default function ClusterDemographicsGrid({ demographics }: Props) {
  const classes = useClasses(ClusterDemographicsGridStyles, {
    name: "ClusterDemographicsGrid",
  });

  const femalePct = demographics.gender.F ?? 0;
  const malePct = demographics.gender.M ?? 0;
  const genderData = [
    { name: "Female", value: femalePct, tooltip: `Female: ${femalePct}%` },
    { name: "Male", value: malePct, tooltip: `Male: ${malePct}%` },
  ];

  const maritalData = mapDistribution(demographics.marital, MARITAL_LABELS, MARITAL_ORDER);
  const smokingData = mapDistribution(demographics.smoking, SMOKING_LABELS, SMOKING_ORDER);
  const burdenData = mapDistribution(demographics.conditionBurden, BURDEN_LABELS, BURDEN_ORDER);

  return (
    <div className={classes.card}>
      <p className={classes.sectionTitle}>Demographics</p>
      <div className={classes.grid}>
        <BarChartComponent
          title="Gender"
          data={genderData}
          colors={[
            theme.colors.charts.gender.female,
            theme.colors.charts.gender.male,
          ]}
        />
        <PieChartComponent title="Marital Status" data={maritalData} />
        <PieChartComponent title="Smoking Status" data={smokingData} />
        <PieChartComponent
          title="Condition Burden"
          data={burdenData}
          colors={BURDEN_COLORS}
        />
      </div>
    </div>
  );
}
