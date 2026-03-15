"use client";

import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";

const statisticsTabs = [
  { name: "PATIENTS", forward: "/statistics/patients" },
  { name: "ALLERGIES", forward: "/statistics/allergies" },
  { name: "CONDITIONS", forward: "/statistics/conditions" },
  { name: "ENCOUNTERS", forward: "/statistics/encounters" },
  { name: "IMMUNIZATIONS", forward: "/statistics/immunizations" },
  { name: "MEDICATIONS", forward: "/statistics/medications" },
  { name: "OBSERVATIONS", forward: "/statistics/observations" },
  { name: "ORGANIZATIONS", forward: "/statistics/organizations" },
  { name: "PROCEDURES", forward: "/statistics/procedures" },
  { name: "PROVIDERS", forward: "/statistics/providers" },
];

export default function StatisticsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "12px 16px" }}>
        <StyledTabs items={statisticsTabs} />
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "0 16px 16px" }}>
        {children}
      </div>
    </div>
  );
}
