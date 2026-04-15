"use client";

import { RootState, AppDispatch } from "@/store";
import { getCareplansStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { CareplansPageStyles } from "./CareplansPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function CareplansPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.careplansStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(CareplansPageStyles, { name: "CareplansPage" });

  useEffect(() => {
    dispatch(getCareplansStatistics());
  }, [dispatch]);

  if (loading) {
    return <div className={classes.loading}>Loading care plan statistics...</div>;
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
          <div className={classes.summaryLabel}>Total Care Plans</div>
          <div className={classes.summaryValue}>
            {data.totalCareplans.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Care Plans</div>
          <div className={classes.summaryValue}>
            {data.uniqueCareplans.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.perPatient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Care Plans per Patient</h3>
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

      <div className={classes.grid}>
        <PieChartComponent
          data={data.activeVsEnded}
          title="Active vs Ended"
          colors={["#3a4555", "#028fb0"]}
        />
        <BarChartComponent
          data={data.topCareplans}
          title="Top 15 Care Plans"
          color="#006780"
          bottomBorder={-20}
        />
      </div>
    </div>
  );
}
