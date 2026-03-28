"use client";

import { RootState, AppDispatch } from "@/store";
import { getAllergiesStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { AllergiesPageStyles } from "./AllergiesPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function AllergiesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.allergiesStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(AllergiesPageStyles, { name: "AllergiesPage" });

  useEffect(() => {
    dispatch(getAllergiesStatistics());
  }, [dispatch]);

  if (loading) {
    return <div className={classes.loading}>Loading allergy statistics...</div>;
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
          <div className={classes.summaryLabel}>Total Allergies</div>
          <div className={classes.summaryValue}>
            {data.total_allergies.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Allergies</div>
          <div className={classes.summaryValue}>
            {data.unique_allergies.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.per_patient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Allergies per Patient</h3>
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
          data={data.top_allergies}
          title="Top 15 Allergies"
          color="#006780"
          bottomBorder={-20}
        />
      </div>
    </div>
  );
}
