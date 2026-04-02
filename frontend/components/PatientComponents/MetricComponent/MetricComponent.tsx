import useClasses from "@/utils/useClasses";
import { MetricComponentStyles } from "./MetricComponentStyles";

interface MetricComponentProps {
  label: string;
  value: React.ReactNode;
  unit?: string;
}

export default function MetricComponent({ label, value, unit }: MetricComponentProps) {
  const classes = useClasses(MetricComponentStyles, { name: "MetricComponent" });

  return (
    <div className={classes.metricBox}>
      <p className={classes.metricLabel}>{label}</p>
      <p className={classes.metricValue}>
        {value ?? "-"}
        {unit && value !== null && (
          <span className={classes.metricUnit}>{unit}</span>
        )}
      </p>
    </div>
  );
}
