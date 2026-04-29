"use client";

import { RootState, AppDispatch } from "@/store";
import { getProvidersStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { ProvidersPageStyles } from "./ProvidersPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ProvidersPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.providersStatistics,
  );
  const range = useSelector((state: RootState) => state.statisticsRange.range);
  const dispatch = useAppDispatch();
  const classes = useClasses(ProvidersPageStyles, { name: "ProvidersPage" });

  useEffect(() => {
    dispatch(getProvidersStatistics(range));
  }, [dispatch, range]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading doctor data...</div>
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
          <div className={classes.summaryLabel}>Total Doctors</div>
          <div className={classes.summaryValue}>
            {data.totalProviders.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Specialties</div>
          <div className={classes.summaryValue}>
            {data.uniqueSpecialities.toLocaleString()}
          </div>
        </div>
      </div>

      <div className={classes.utilizationCard}>
        <h3 className={classes.utilizationTitle}>Patient Load</h3>
        <div className={classes.utilizationStats}>
          <div>
            <div className={classes.utilizationStatLabel}>Min</div>
            <div className={classes.utilizationStatValue}>
              {data.utilization.min}
            </div>
          </div>
          <div>
            <div className={classes.utilizationStatLabel}>Avg</div>
            <div className={classes.utilizationStatValue}>
              {data.utilization.avg}
            </div>
          </div>
          <div>
            <div className={classes.utilizationStatLabel}>Median</div>
            <div className={classes.utilizationStatValue}>
              {data.utilization.median}
            </div>
          </div>
          <div>
            <div className={classes.utilizationStatLabel}>Max</div>
            <div className={classes.utilizationStatValue}>
              {data.utilization.max}
            </div>
          </div>
        </div>
      </div>

      <div className={classes.grid}>
        <PieChartComponent data={data.gender} title="Gender Distribution" />
        <BarChartComponent
          data={data.topCities}
          title="Top 10 Cities"
          color="#006780"
          bottomBorder={-20}
        />
      </div>
    </div>
  );
}
