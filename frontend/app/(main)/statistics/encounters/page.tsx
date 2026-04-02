"use client";

import { RootState, AppDispatch } from "@/store";
import { getEncountersStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { EncountersPageStyles } from "./EncountersPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

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
      <div className={classes.loading}>Loading encounter statistics...</div>
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
        <div className={classes.totalLabel}>Total Encounters</div>
        <div className={classes.totalValue}>
          {data.totalEncounters.toLocaleString()}
        </div>
      </div>

      <div className={classes.grid}>
        <PieChartComponent
          data={data.encounterClass}
          title="Encounter Class Distribution"
          colors={[
            "#006780",
            "#028fb0",
            "#6cd3f7",
            "#3a4555",
            "#515f74",
            "#b7eaff",
          ]}
        />
        <BarChartComponent
          data={data.topDescriptions}
          title="Top Descriptions"
          color="#006780"
          bottomBorder={-20}
        />

        <div className={classes.durationTable}>
          <h3 className={classes.durationTitle}>
            Duration Stats per Encounter Class (minutes)
          </h3>
          <table className={classes.table}>
            <thead>
              <tr>
                <th className={classes.th}>Class</th>
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
          title="Top Reason Descriptions"
          color="#028fb0"
          showLabel
          bottomBorder={-10}
        />
      </div>
    </div>
  );
}
