"use client";

import { usePathname } from "next/navigation";
import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";
import useClasses from "@/utils/useClasses";
import { ClustersLayoutStyles } from "./styles";

const clusterTabs = [
  { name: "PATIENT GROUPS", forward: "/clusters/summaries" },
  { name: "GROUP STATISTICS", forward: "/clusters/statistics" },
  {
    name: "NUMERICAL GROUP FEATURES",
    forward: "/clusters/numerical-features",
  },
  {
    name: "CATEGORICAL GROUP FEATURES",
    forward: "/clusters/categorical-features",
  },
];

export default function ClustersLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const classes = useClasses(ClustersLayoutStyles, { name: "ClustersLayout" });
  const pathname = usePathname();
  const isDetailRoute = /^\/clusters\/-?\d+(\/|$)/.test(pathname ?? "");

  return (
    <div className={classes.container}>
      {!isDetailRoute && (
        <div className={classes.tabsWrapper}>
          <StyledTabs items={clusterTabs} />
        </div>
      )}
      <div className={classes.content}>{children}</div>
    </div>
  );
}
