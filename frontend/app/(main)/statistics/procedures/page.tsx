"use client";

import { RootState, AppDispatch } from "@/store";
import { getProceduresStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { ProceduresPageStyles } from "./ProceduresPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ProceduresPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.proceduresStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ProceduresPageStyles, { name: "ProceduresPage" });

  useEffect(() => {
    dispatch(getProceduresStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading procedure statistics...</div>
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
          <div className={classes.summaryLabel}>Total Procedures</div>
          <div className={classes.summaryValue}>
            {data.totalProcedures.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Procedures</div>
          <div className={classes.summaryValue}>
            {data.uniqueProcedures.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.perPatient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Procedures per Patient</h3>
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
          data={data.topProcedures}
          title="Top 20 Procedures"
          color="#006780"
          showLabel
          bottomBorder={-8}
        />
      </div>
    </div>
  );
}
