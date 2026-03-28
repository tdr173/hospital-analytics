"use client";

import { RootState, AppDispatch } from "@/store";
import { getMedicationsStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { MedicationsPageStyles } from "./MedicationsPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function MedicationsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.medicationsStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(MedicationsPageStyles, {
    name: "MedicationsPage",
  });

  useEffect(() => {
    dispatch(getMedicationsStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading medication statistics...</div>
    );
  }

  if (error) {
    return <div className={classes.error}>{error}</div>;
  }

  if (!data) {
    return null;
  }

  return (
    <div className={classes.container} style={{ paddingTop: 24 }}>
      <div className={classes.summaryRow}>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Total Medications</div>
          <div className={classes.summaryValue}>
            {data.total_medications.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Medications</div>
          <div className={classes.summaryValue}>
            {data.unique_medications.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.per_patient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Medications per Patient</h3>
        <div className={classes.perPatientStats}>
          <div>
            <div className={classes.perPatientStatLabel}>Min</div>
            <div className={classes.perPatientStatValue}>
              {data.per_patient.min}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Avg</div>
            <div className={classes.perPatientStatValue}>
              {data.per_patient.avg}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Max</div>
            <div className={classes.perPatientStatValue}>
              {data.per_patient.max}
            </div>
          </div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Duration (Days)</h3>
        <div className={classes.perPatientStats}>
          <div>
            <div className={classes.perPatientStatLabel}>Min</div>
            <div className={classes.perPatientStatValue}>
              {data.duration_stats.min_duration}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Avg</div>
            <div className={classes.perPatientStatValue}>
              {data.duration_stats.avg_duration}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Median</div>
            <div className={classes.perPatientStatValue}>
              {data.duration_stats.median_duration}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Max</div>
            <div className={classes.perPatientStatValue}>
              {data.duration_stats.max_duration}
            </div>
          </div>
        </div>
      </div>

      <div className={classes.grid}>
        <PieChartComponent
          data={data.active_vs_ended}
          title="Active vs Ended"
          colors={["#3a4555", "#028fb0"]}
        />
        <BarChartComponent
          data={data.top_medications.slice(0, 15)}
          title="Top 15 Medications"
          color="#006780"
          bottomBorder={-20}
        />
      </div>
    </div>
  );
}
