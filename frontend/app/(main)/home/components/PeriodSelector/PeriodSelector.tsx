"use client";

import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "@/store";
import { setDashboardRange } from "@/store/slices/dashboard/dashboard-slice";
import { DashboardRange } from "@/models/generic/dashboard";
import useClasses from "@/utils/useClasses";
import { PeriodSelectorStyles } from "./PeriodSelectorStyles";

const PERIODS: { label: string; value: DashboardRange }[] = [
  { label: "Week", value: "week" },
  { label: "Month", value: "month" },
  { label: "Year", value: "year" },
  { label: "All Time", value: "all" },
];

export default function PeriodSelector() {
  const dispatch = useDispatch<AppDispatch>();
  const selected = useSelector((s: RootState) => s.dashboard.selectedRange);
  const role = useSelector((s: RootState) => s.auth.user?.role);
  const classes = useClasses(PeriodSelectorStyles, { name: "PeriodSelector" });

  // "All Time" is only meaningful for the hospital-wide manager view.
  const periods = role === "MANAGER" ? PERIODS : PERIODS.filter((p) => p.value !== "all");

  return (
    <div className={classes.rangeGroup}>
      {periods.map(({ label, value }) => {
        const active = selected === value;
        return (
          <button
            key={value}
            type="button"
            className={
              active
                ? `${classes.rangeButton} ${classes.rangeButtonActive}`
                : classes.rangeButton
            }
            onClick={() => dispatch(setDashboardRange(value))}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
