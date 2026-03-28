"use client";

import { RootState, AppDispatch } from "@/store";
import { getConditionsStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { ConditionsPageStyles } from "./ConditionsPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ConditionsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.conditionsStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ConditionsPageStyles, { name: "ConditionsPage" });

  useEffect(() => {
    dispatch(getConditionsStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading condition statistics...</div>
    );
  }

  if (error) {
    return <div className={classes.error}>{error}</div>;
  }

  if (!data) {
    return null;
  }

  return (
    <div className={classes.container}>
      <div className={classes.summaryRow}>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Total Conditions</div>
          <div className={classes.summaryValue}>
            {data.total_conditions.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Conditions</div>
          <div className={classes.summaryValue}>
            {data.unique_conditions.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.per_patient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Conditions per Patient</h3>
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

      <div className={classes.grid}>
        <PieChartComponent
          data={data.active_vs_resolved}
          title="Active vs Resolved"
          colors={["#3a4555", "#028fb0"]}
        />
        <BarChartComponent
          data={data.top_conditions}
          title="Top 20 Conditions"
          color="#006780"
          bottomBorder={-20}
        />
      </div>
    </div>
  );
}
