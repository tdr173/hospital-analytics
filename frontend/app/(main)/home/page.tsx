"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";

import { RootState, AppDispatch } from "@/store";
import { fetchDashboard } from "@/store/slices/dashboard/thunks";
import { DashboardRange } from "@/models/generic/dashboard";
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
import PeriodSelector from "./components/PeriodSelector/PeriodSelector";
import PatientSelfView from "@/components/PatientSelfView/PatientSelfView";
import PracticeLlmSummaryCard from "@/components/PracticeLlmSummaryCard/PracticeLlmSummaryCard";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const RANGE_LABELS: Record<DashboardRange, string> = {
  week: "Last Week",
  month: "Last Month",
  year: "Last Year",
  all: "All Time",
};

export default function HomePage() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(HomePageStyles, { name: "HomePage" });

  const role = useSelector((s: RootState) => s.auth.user?.role);
  const { data, loading, error, selectedRange } = useSelector(
    (state: RootState) => state.dashboard,
  );

  useEffect(() => {
    if (role === "PATIENT") return;
    if (!data) dispatch(fetchDashboard(selectedRange));
  }, [data, dispatch, role, selectedRange]);

  if (role === "PATIENT") {
    return <PatientSelfView />;
  }

  if (loading) return <div className={classes.loading}>Loading...</div>;
  if (error) return <div className={classes.error}>{error}</div>;
  if (!data) return null;

  const rangeLabel = RANGE_LABELS[selectedRange];

  if (role === "DOCTOR") {
    return (
      <div className={classes.container}>
        <PeriodSelector />

        <PracticeLlmSummaryCard />

        <DailyEncounterChart
          data={data.encountersTimeline}
          title={`Visit Volume - ${rangeLabel}`}
          monthly={selectedRange === "year"}
          hideXLabels={selectedRange === "month"}
        />

        <div className={classes.splitRow}>
          <TopConditionsBar
            data={data.topConditions}
            title={`Top 10 Conditions - ${rangeLabel}`}
          />
          <LastWeekClassPie
            data={data.encounterByClass}
            title={`${rangeLabel} - Visits by Type`}
          />
        </div>

        <RecentEncountersTable
          data={data.recentEncounters}
          onPatientClick={(id) => router.push(`/patients/${id}`)}
          onEncounterClick={(id) => router.push(`/encounters/${id}`)}
        />
      </div>
    );
  }

  return (
    <div className={classes.container}>
      <PeriodSelector />

      <KpiPrimaryRow kpis={data.kpis} />

      <div className={classes.splitRow}>
        <SecondaryKpiGrid kpis={data.kpis} periodLabel={rangeLabel} />
        <LastWeekClassPie
          data={data.encounterByClass}
          title={`${rangeLabel} - Visits by Type`}
        />
      </div>

      <DailyEncounterChart
        data={data.encountersTimeline}
        title="Visit Volume - Last Year"
        monthly
      />

      <div className={classes.pieSplitRow}>
        <AgeGroupsPie data={data.ageGroups} />
        <GenderPie data={data.genderDistribution} />
      </div>

      <RecentEncountersTable
        data={data.recentEncounters}
        onPatientClick={(id) => router.push(`/patients/${id}`)}
        onEncounterClick={(id) => router.push(`/encounters/${id}`)}
      />

      {role === "MANAGER" && (
        <>
          <TopConditionsBar
            data={data.topConditions}
            title={`Top 10 Conditions - ${rangeLabel}`}
          />
          <ClusterDistributionCard data={data.clusterDistribution} />
        </>
      )}
    </div>
  );
}
