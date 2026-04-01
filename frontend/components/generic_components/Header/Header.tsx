"use client";

import useClasses from "@/utils/useClasses";
import headerStyles from "./HeaderStyles";
import UserTypeTag from "../../UserTypeTag/UserTypeTag";
import { usePathname } from "next/navigation";

const ROUTE_TITLES: Record<string, string> = {
  "/statistics": "Dataset Statistics",
  "/clusters/summaries": "Clusters - Summaries",
  "/clusters/statistics": "Clusters - Statistics",
  "/clusters": "Clusters",
};

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export default function Header() {
  const classes = useClasses(headerStyles, { name: "HeaderStyles" });
  const pathname = usePathname();

  const matchedKey = Object.keys(ROUTE_TITLES)
    .sort((a, b) => b.length - a.length)
    .find((key) => pathname.startsWith(key));

  const title = matchedKey
    ? ROUTE_TITLES[matchedKey]
    : pathname.split("/").filter(Boolean).map(capitalize).join(" - ");

  return (
    <div className={classes.headerContainer}>
      <span className={classes.pageTitle}>{title}</span>
      <UserTypeTag userType="admin" />
    </div>
  );
}
