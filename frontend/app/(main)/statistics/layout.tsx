"use client";

import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";

const statisticsTabs = [
  { name: "PATIENTS", forward: "/statistics/patients" },
  { name: "ENCOUNTERS", forward: "/statistics/encounters" },
  { name: "CONDITIONS", forward: "/statistics/conditions" },
  { name: "OBSERVATIONS", forward: "/statistics/observations" },
  { name: "MEDICATIONS", forward: "/statistics/medications" },
  { name: "PROCEDURES", forward: "/statistics/procedures" },
  { name: "IMMUNIZATIONS", forward: "/statistics/immunizations" },
  { name: "ALLERGIES", forward: "/statistics/allergies" },
  { name: "ORGANIZATIONS", forward: "/statistics/organizations" },
  { name: "PROVIDERS", forward: "/statistics/providers" },
];

export default function StatisticsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "0 16px" }}>
        <StyledTabs items={statisticsTabs} />
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "0 16px" }}>
        {children}
      </div>
    </div>
  );
}
