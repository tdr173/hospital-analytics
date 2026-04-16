"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";

import { RootState, AppDispatch } from "@/store";
import { fetchDashboard } from "@/store/slices/dashboard/thunks";
import useClasses from "@/utils/useClasses";
import { HomePageStyles } from "./styles";

import KpiPrimaryRow from "./components/KpiPrimaryRow/KpiPrimaryRow";
import SecondaryKpiGrid from "./components/SecondaryKpiGrid/SecondaryKpiGrid";
import LastWeekClassPie from "./components/LastWeekClassPie/LastWeekClassPie";
import DailyEncounterChart from "./components/DailyEncounterChart/DailyEncounterChart";
import AgeGroupsPie from "./components/AgeGroupsPie/AgeGroupsPie";
import GenderPie from "./components/GenderPie/GenderPie";
import RecentEncountersTable from "./components/RecentEncountersTable/RecentEncountersTable";
import TopConditionsBar from "./components/TopConditionsBar/TopConditionsBar";
import ClusterDistributionCard from "./components/ClusterDistributionCard/ClusterDistributionCard";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function HomePage() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(HomePageStyles, { name: "HomePage" });

  const { data, loading, error } = useSelector(
    (state: RootState) => state.dashboard,
  );

  useEffect(() => {
    if (!data) dispatch(fetchDashboard());
  }, [data, dispatch]);

  if (loading) return <div className={classes.loading}>Loading dashboard...</div>;
  if (error) return <div className={classes.error}>{error}</div>;
  if (!data) return null;

  return (
    <div className={classes.container}>
      <KpiPrimaryRow kpis={data.kpis} />

      <div className={classes.splitRow}>
        <SecondaryKpiGrid kpis={data.kpis} />
        <LastWeekClassPie data={data.lastWeekEncounterByClass} />
      </div>

      <DailyEncounterChart data={data.lastMonthEncounters} />

      <div className={classes.pieSplitRow}>
        <AgeGroupsPie data={data.ageGroups} />
        <GenderPie data={data.genderDistribution} />
      </div>

      <RecentEncountersTable
        data={data.recentEncounters}
        onPatientClick={(id) => router.push(`/patients/${id}`)}
      />

      <TopConditionsBar data={data.topConditionsLastWeek} />

      <ClusterDistributionCard data={data.clusterDistribution} />
    </div>
  );
}
