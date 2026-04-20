"use client";

import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";
import useClasses from "@/utils/useClasses";
import { StatisticsLayoutStyles } from "./styles";

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
  { name: "FACILITIES", forward: "/statistics/organizations" },
  { name: "DOCTORS", forward: "/statistics/providers" },
];

export default function StatisticsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const classes = useClasses(StatisticsLayoutStyles, { name: "StatisticsLayout" });

  return (
    <div className={classes.container}>
      <div className={classes.tabsWrapper}>
        <StyledTabs items={statisticsTabs} />
      </div>
      <div className={classes.content}>
        {children}
      </div>
    </div>
  );
}
