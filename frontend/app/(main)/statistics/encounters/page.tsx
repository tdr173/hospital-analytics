"use client";

import { RootState, AppDispatch } from "@/store";
import { getEncountersStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { EncountersPageStyles } from "./EncountersPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function EncountersPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.encountersStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(EncountersPageStyles, { name: "EncountersPage" });

  useEffect(() => {
    dispatch(getEncountersStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading visit data...</div>
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
      <div className={classes.totalCard}>
        <div className={classes.totalLabel}>Total Visits</div>
        <div className={classes.totalValue}>
          {data.totalEncounters.toLocaleString()}
        </div>
      </div>

      <div className={classes.grid}>
        <PieChartComponent
          data={data.encounterClass}
          title="Visit Type Distribution"
          colors={data.encounterClass.map(
            (d) =>
              theme.colors.charts.encounterClass[d.name.toLowerCase()] ??
              theme.colors.charts.encounterClass.other,
          )}
        />
        <BarChartComponent
          data={data.topDescriptions}
          title="Top Visit Reasons"
          color={theme.colors.primary.main}
          bottomBorder={-20}
        />

        <div className={classes.durationTable}>
          <h3 className={classes.durationTitle}>
            Visit Duration by Type (minutes)
          </h3>
          <table className={classes.table}>
            <thead>
              <tr>
                <th className={classes.th}>Visit Type</th>
                <th className={classes.th}>Count</th>
                <th className={classes.th}>Min</th>
                <th className={classes.th}>Max</th>
                <th className={classes.th}>Avg</th>
              </tr>
            </thead>
            <tbody>
              {data.durationStats.map((row) => (
                <tr key={row.name}>
                  <td className={classes.td}>{row.name}</td>
                  <td className={classes.td}>{row.count.toLocaleString()}</td>
                  <td className={classes.td}>{row.minDuration}</td>
                  <td className={classes.td}>{row.maxDuration}</td>
                  <td className={classes.td}>{row.avgDuration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={classes.fullWidthChart}>
        <BarChartComponent
          data={data.topReasonDescriptions}
          title="Top Visit Reasons"
          color={theme.colors.primary.light}
          showLabel
          bottomBorder={-10}
        />
      </div>
    </div>
  );
}
