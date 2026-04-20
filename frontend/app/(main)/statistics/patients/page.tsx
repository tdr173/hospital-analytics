"use client";

import { RootState, AppDispatch } from "@/store";
import { getPatientsStatistics } from "@/store/slices/statistics/thunks";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import { PatientsPageStyles } from "./PatientsPageStyles";
import BarChartComponent from "@/components/generic_components/BarChartComponent/BarChartComponent";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function PatientsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.patientsStatistics,
  );
  const range = useSelector((state: RootState) => state.statisticsRange.range);
  const dispatch = useAppDispatch();
  const classes = useClasses(PatientsPageStyles, { name: "PatientsPage" });

  useEffect(() => {
    dispatch(getPatientsStatistics(range));
  }, [dispatch, range]);

  if (loading) {
    return <div className={classes.loading}>Loading patient data...</div>;
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
        <div className={classes.totalLabel}>Total Patients</div>
        <div className={classes.totalValue}>
          {data.totalPatients.toLocaleString()}
        </div>
      </div>

      <div className={classes.grid}>
        <BarChartComponent
          data={data.ageGroups}
          title="Age Groups"
          color="#006780"
        />
        <PieChartComponent
          data={data.gender}
          title="Gender Distribution"
          colors={data.gender.map((d) =>
            d.name === "M"
              ? theme.colors.gender.male
              : d.name === "F"
                ? theme.colors.gender.female
                : theme.colors.primary.main,
          )}
        />
        <PieChartComponent data={data.race} title="Race Distribution" />
        <PieChartComponent
          data={data.ethnicity}
          title="Ethnicity Distribution"
          colors={["#006780", "#028fb0", "#6cd3f7"]}
        />
        <PieChartComponent
          data={data.maritalStatus}
          title="Marital Status"
          colors={["#006780", "#028fb0", "#6cd3f7", "#515f74"]}
        />
        <PieChartComponent
          data={data.vitalStatus}
          title="Vital Status"
          colors={["#028fb0", "#515f74"]}
        />
      </div>

      <div className={classes.fullWidthChart}>
        <BarChartComponent
          data={data.topCities}
          title="Top Cities"
          color="#515f74"
          showLabel
          bottomBorder={-20}
        />
      </div>
    </div>
  );
}
