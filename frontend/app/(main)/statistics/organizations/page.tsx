"use client";

import { RootState, AppDispatch } from "@/store";
import { getOrganizationsStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { OrganizationsPageStyles } from "./OrganizationsPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function OrganizationsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.organizationsStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(OrganizationsPageStyles, {
    name: "OrganizationsPage",
  });

  useEffect(() => {
    dispatch(getOrganizationsStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading organization statistics...</div>
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
      <div className={classes.summaryCard}>
        <div className={classes.summaryLabel}>Total Organizations</div>
        <div className={classes.summaryValue}>
          {data.totalOrganizations.toLocaleString()}
        </div>
      </div>

      <div className={classes.utilizationCard}>
        <h3 className={classes.utilizationTitle}>Utilization</h3>
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

      <div className={classes.chartContainer}>
        <BarChartComponent
          data={data.topCities}
          title="Top 10 Cities"
          color="#006780"
          showLabel
          bottomBorder={-5}
        />
      </div>
    </div>
  );
}
