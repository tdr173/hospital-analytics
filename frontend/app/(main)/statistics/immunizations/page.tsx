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
  const range = useSelector((state: RootState) => state.statisticsRange.range);
  const dispatch = useAppDispatch();
  const classes = useClasses(ImmunizationsPageStyles, {
    name: "ImmunizationsPage",
  });

  useEffect(() => {
    dispatch(getImmunizationsStatistics(range));
  }, [dispatch, range]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading vaccination data...</div>
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
          <div className={classes.summaryLabel}>Total Vaccinations</div>
          <div className={classes.summaryValue}>
            {data.totalImmunizations.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Vaccinations</div>
          <div className={classes.summaryValue}>
            {data.uniqueImmunizations.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.perPatient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Vaccinations per Patient</h3>
        <div className={classes.perPatientStats}>
          <div>
            <div className={classes.perPatientStatLabel}>Min</div>
            <div className={classes.perPatientStatValue}>
              {data.perPatient.min}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Avg</div>
            <div className={classes.perPatientStatValue}>
              {data.perPatient.avg}
            </div>
          </div>
          <div>
            <div className={classes.perPatientStatLabel}>Max</div>
            <div className={classes.perPatientStatValue}>
              {data.perPatient.max}
            </div>
          </div>
        </div>
      </div>

      <div className={classes.chartContainer}>
        <BarChartComponent
          data={data.topImmunizations}
          title="Top 15 Vaccinations"
          color="#006780"
          showLabel
          bottomBorder={-8}
        />
      </div>
    </div>
  );
}
