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
            {data.totalObservations.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Unique Types</div>
          <div className={classes.summaryValue}>
            {data.uniqueObservationTypes.toLocaleString()}
          </div>
        </div>
        <div className={classes.summaryCard}>
          <div className={classes.summaryLabel}>Avg per Patient</div>
          <div className={classes.summaryValue}>{data.perPatient.avg}</div>
        </div>
      </div>

      <div className={classes.perPatientCard}>
        <h3 className={classes.perPatientTitle}>Observations per Patient</h3>
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

      <div className={classes.chartSection}>
        <BarChartComponent
          data={data.topObservationTypes}
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
              {data.numericStats.map((row) => (
                <tr key={row.name}>
                  <td className={classes.tdFirst}>{row.name}</td>
                  <td className={classes.td}>{row.count.toLocaleString()}</td>
                  <td className={classes.td}>
                    {row.patientCount.toLocaleString()}
                  </td>
                  <td className={classes.td}>{row.percentage}%</td>
                  <td className={classes.td}>{row.minValue}</td>
                  <td className={classes.td}>{row.maxValue}</td>
                  <td className={classes.td}>{row.avgValue}</td>
                  <td className={classes.td}>{row.units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.categoricalStats && data.categoricalStats.length > 0 && (
        <div className={classes.gridWithMargin}>
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
                {data.categoricalStats.map((row) => (
                  <tr key={row.name}>
                    <td className={classes.tdFirst}>{row.name}</td>
                    <td className={classes.td}>
                      {row.count?.toLocaleString()}
                    </td>
                    <td className={classes.td}>
                      {row.patientCount?.toLocaleString()}
                    </td>
                    <td className={classes.td}>{row.percentage}%</td>
                    <td className={classes.td}>{row.distinctValues}</td>
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
