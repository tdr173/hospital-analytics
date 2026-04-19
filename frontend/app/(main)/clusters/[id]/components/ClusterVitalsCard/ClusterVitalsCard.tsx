"use client";

import useClasses from "@/utils/useClasses";
import { ClusterVitals } from "@/models/generic/clusters";
import { ClusterVitalsCardStyles } from "./ClusterVitalsCardStyles";

interface Props {
  vitals: ClusterVitals;
}

interface VitalSpec {
  label: string;
  value: number;
  unit?: string;
}

export default function ClusterVitalsCard({ vitals }: Props) {
  const classes = useClasses(ClusterVitalsCardStyles, { name: "ClusterVitalsCard" });

  const items: VitalSpec[] = [
    { label: "Avg Age", value: vitals.avgAge, unit: "yrs" },
    { label: "Avg BMI", value: vitals.avgBmi },
    { label: "Avg Systolic BP", value: vitals.avgSystolicBp, unit: "mmHg" },
    { label: "Avg Glucose", value: vitals.avgGlucose, unit: "mg/dL" },
    { label: "Avg QALY", value: vitals.avgQaly },
    { label: "Avg DALY", value: vitals.avgDaly },
  ];

  return (
    <div className={classes.card}>
      <p className={classes.sectionTitle}>Group Vital Averages</p>
      <div className={classes.grid}>
        {items.map((item) => (
          <div key={item.label} className={classes.statBox}>
            <div className={classes.statLabel}>{item.label}</div>
            <div className={classes.statValue}>
              {item.value}
              {item.unit && <span className={classes.statUnit}>{item.unit}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
