"use client";

import { RootState, AppDispatch } from "@/store";
import { getObservationsStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { ObservationsPageStyles } from "./ObservationsPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ObservationsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.observationsStatistics,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ObservationsPageStyles, {
    name: "ObservationsPage",
  });

  useEffect(() => {
    dispatch(getObservationsStatistics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className={classes.loading}>Loading observation statistics...</div>
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
          <div className={classes.summaryLabel}>Total Observations</div>
          <div className={classes.summaryValue}>
            {data.total_observations.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Types</div>
          <div className={classes.summaryValue}>
            {data.unique_observation_types.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.per_patient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Observations per Patient</h3>
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

      <div className={classes.chartSection}>
        <BarChartComponent
          data={data.top_observation_types}
          title="Top Numeric Observation Types"
          color="#006780"
          showLabel
          bottomBorder={-10}
        />
      </div>

      <div className={classes.grid}>
        <div className={classes.numericTable}>
          <h3 className={classes.numericTitle}>
            Numeric Stats per Observation Type
          </h3>
          <table className={classes.table}>
            <thead>
              <tr>
                <th className={classes.thFirst}>Observation</th>
                <th className={classes.th}>Records</th>
                <th className={classes.th}>Patients</th>
                <th className={classes.th}>Patient %</th>
                <th className={classes.th}>Min</th>
                <th className={classes.th}>Max</th>
                <th className={classes.th}>Avg</th>
                <th className={classes.th}>Units</th>
              </tr>
            </thead>
            <tbody>
              {data.numeric_stats.map((row) => (
                <tr key={row.name}>
                  <td className={classes.tdFirst}>{row.name}</td>
                  <td className={classes.td}>{row.count.toLocaleString()}</td>
                  <td className={classes.td}>
                    {row.patient_count.toLocaleString()}
                  </td>
                  <td className={classes.td}>{row.percentage}%</td>
                  <td className={classes.td}>{row.min_value}</td>
                  <td className={classes.td}>{row.max_value}</td>
                  <td className={classes.td}>{row.avg_value}</td>
                  <td className={classes.td}>{row.units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.categorical_stats && data.categorical_stats.length > 0 && (
        <div className={classes.grid} style={{ marginTop: 24 }}>
          <div className={classes.numericTable}>
            <h3 className={classes.numericTitle}>Categorical Observations</h3>
            <table className={classes.table}>
              <thead>
                <tr>
                  <th className={classes.thFirst}>Observation</th>
                  <th className={classes.th}>Records</th>
                  <th className={classes.th}>Patients</th>
                  <th className={classes.th}>Patient %</th>
                  <th className={classes.th}>Distinct Values</th>
                </tr>
              </thead>
              <tbody>
                {data.categorical_stats.map((row) => (
                  <tr key={row.name}>
                    <td className={classes.tdFirst}>{row.name}</td>
                    <td className={classes.td}>
                      {row.count?.toLocaleString()}
                    </td>
                    <td className={classes.td}>
                      {row.patient_count?.toLocaleString()}
                    </td>
                    <td className={classes.td}>{row.percentage}%</td>
                    <td className={classes.td}>{row.distinct_values}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
