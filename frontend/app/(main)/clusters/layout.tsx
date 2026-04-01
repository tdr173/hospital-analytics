"use client";

import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";

const clusterTabs = [
  { name: "CLUSTER SUMMARIES", forward: "/clusters/summaries" },
  { name: "CLUSTER STATISTICS", forward: "/clusters/statistics" },
  { name: "NUMERIC CLUSTER FEATURES", forward: "/clusters/numeric-features" },
  { name: "CATEGORICAL CLUSTER FEATURES", forward: "/clusters/categorical-features" },
];

export default function ClustersLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}>
      <div style={{ padding: "0 16px", overflow: "hidden", minWidth: 0 }}>
        <StyledTabs items={clusterTabs} />
      </div>
      <div style={{ flex: 1, overflow: "auto" }}>
        {children}
      </div>
    </div>
  );
}
