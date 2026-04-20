"use client";

import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";
import useClasses from "@/utils/useClasses";
import { StatisticsLayoutStyles } from "./styles";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "@/store";
import {
  StatisticsRange,
  setStatisticsRange,
} from "@/store/slices/statistics/range-slice";

const statisticsTabs = [
  { name: "PATIENTS", forward: "/statistics/patients" },
  { name: "VISITS", forward: "/statistics/encounters" },
  { name: "CONDITIONS", forward: "/statistics/conditions" },
  { name: "TEST RESULTS", forward: "/statistics/observations" },
  { name: "MEDICATIONS", forward: "/statistics/medications" },
  { name: "PROCEDURES", forward: "/statistics/procedures" },
  { name: "VACCINATIONS", forward: "/statistics/immunizations" },
  { name: "ALLERGIES", forward: "/statistics/allergies" },
  { name: "CARE PLANS", forward: "/statistics/careplans" },
  { name: "DOCTORS", forward: "/statistics/providers" },
];

const rangeOptions: { label: string; value: StatisticsRange }[] = [
  { label: "Last week", value: "week" },
  { label: "Last month", value: "month" },
  { label: "All time", value: "all" },
];

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function StatisticsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const classes = useClasses(StatisticsLayoutStyles, { name: "StatisticsLayout" });
  const dispatch = useAppDispatch();
  const range = useSelector((s: RootState) => s.statisticsRange.range);

  return (
    <div className={classes.container}>
      <div className={classes.topBar}>
        <div className={classes.tabsWrapper}>
          <StyledTabs items={statisticsTabs} />
        </div>
        <div className={classes.rangeGroup}>
          {rangeOptions.map((opt) => {
            const active = range === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                className={
                  active
                    ? `${classes.rangeButton} ${classes.rangeButtonActive}`
                    : classes.rangeButton
                }
                onClick={() => dispatch(setStatisticsRange(opt.value))}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>
      <div className={classes.content}>{children}</div>
    </div>
  );
}
