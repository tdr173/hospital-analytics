"use client";

import { RootState, AppDispatch } from "@/store";
import { getImmunizationsStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { ImmunizationsPageStyles } from "./ImmunizationsPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ImmunizationsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.immunizationsStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ImmunizationsPageStyles, {
    name: "ImmunizationsPage",
  });

  useEffect(() => {
    dispatch(getImmunizationsStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading immunization statistics...</div>
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
          <div className={classes.summaryLabel}>Total Immunizations</div>
          <div className={classes.summaryValue}>
            {data.total_immunizations.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Immunizations</div>
          <div className={classes.summaryValue}>
            {data.unique_immunizations.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.per_patient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Immunizations per Patient</h3>
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

      <div className={classes.chartContainer}>
        <BarChartComponent
          data={data.top_immunizations}
          title="Top 15 Immunizations"
          color="#006780"
          showLabel
          bottomBorder={-8}
        />
      </div>
    </div>
  );
}
